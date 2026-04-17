# Adding a New Logic

This guide explains how to add a new temporal logic to the VITAMIN model checker. Everything lives in one place: formula parsers under `parsers/formulas/`, algorithms under `algorithms/explicit/`, and API config in the backend. Do not use the old layout (`logics/`, `models/`, `model_checker_interface/`).

We use **COTL** as the running example. COTL is a cost-bounded logic that reuses OATL formula syntax (`<1><5>F p`) and the costCGS model type. The steps below refer to COTL so you see real paths and choices.

---

## What the checker must return

Every logic must return a dict the API and tests expect.

**Success:** include `"res"` (e.g. `"Result: {'s0', 's1'}"`) and `"initial_state"` (e.g. `"Initial state s0: True"`).

**Error:** include an `"error"` key. Use the helpers in `model_checker.utils.error_handler`: `create_syntax_error`, `create_semantic_error`, `create_model_error`, `create_system_error`, `create_validation_error`.

**Helpers:** use `format_model_checking_result` and `verify_initial_state` from `algorithms/explicit/shared/result_utils.py` so the format stays consistent. See ATL or OATL for how they are used.

---

## Step 1: Formula parser

You have two options.

**Option A - New parser.** Add a folder `parsers/formulas/<LogicName>/` with a parser (e.g. `parser.py`) and register it in `parsers/formula_parser_factory.py` in `_AVAILABLE_PARSERS`. Good references: `parsers/formulas/ATL/parser.py` and `parsers/formulas/OATL/parser.py`.

**Option B - Reuse an existing parser.** If your logic uses the same formula syntax as another (e.g. COTL uses OATL syntax), do not add a new parser. In `workbench/api/services/model_checking/utils/logic_config.py`, add your logic to `PARSER_MODULE_MAP` and point it at the existing parser module (e.g. `LogicType.COTL` -> `"model_checker.parsers.formulas.OATL.parser"`). The API will then use that parser for your logic.

---

## Step 2: Algorithm

Add a module under `algorithms/explicit/<LogicName>/` (e.g. `COTL.py`).

**Core function.** Implement a function that takes the **model parser** (the object you get after the runner has called `create_model_parser_for_logic` and `read_file`; it holds the in-memory model, e.g. a costCGS instance) and the formula string. This function should:

1. Get the formula parser via `FormulaParserFactory.get_parser_instance("<ParserName>")` (use the parser name you registered or the one in `PARSER_MODULE_MAP`).
2. Parse the formula, build the tree, run your solver, and get the set of states that satisfy the formula.
3. Compute whether the initial state is in that set with `verify_initial_state(initial_state, result_str)`.
4. Return a dict via `format_model_checking_result(result_str, initial_state, is_satisfied)`.

Do not use globals: the model is always the instance passed into this function. For errors (syntax, semantic, etc.), return a dict with an `"error"` key using the helpers in `utils.error_handler`.

**Entry point.** Expose a public function:

`model_checking(formula: str, filename: str) -> Dict[str, Any]`

Inside it, call `execute_model_checking_with_parser(formula, filename, "<LogicType>", _core_xxx_checking)` from `model_checker.engine.runner`. The runner handles validation, file reading, and error handling; it calls your core function with the model parser and the formula.

**Reference.** Copy and adapt from `algorithms/explicit/OATL/OATL.py` or `algorithms/explicit/ATL/ATL.py`. If you have old code under `model_checker_interface/explicit/<Logic>/`, move it into `algorithms/explicit/<Logic>/` and adapt it to receive the model instance from the runner instead of a global.

---

## Step 3: Model type (only if needed)

If your logic uses **CGS**, **costCGS**, or **capCGS**, you only need to tell the model parser factory which logic uses which type.

- **costCGS:** In `parsers/model_parser_factory.py`, add your logic to `COST_BASED_FORMULAS` (e.g. `"COTL"`).
- **capCGS:** Add it to `CAPACITY_BASED_FORMULAS` in the same file.

If your logic needs a **new game structure** (e.g. a new format that is not CGS, costCGS, or capCGS):

1. Add a new package under `parsers/game_structures/<name>/` with a parser (e.g. a class that has `read_file(filename)`), similar to `cgs` or `cost_cgs`.
2. In `model_parser_factory.py`: add detection in `detect_model_type_from_content`, register the new type in `PARSER_CLASSES`, and in `create_model_parser_for_logic` map your logic to this model type.

COTL does not need a new model type; it uses costCGS and is added to `COST_BASED_FORMULAS`.

---

## Step 4: API and config

**Backend schema.** In `workbench/api/schemas/requests.py`, add a constant for your logic (e.g. `COTL = "COTL"`).

**logic_config.yaml** (in `workbench/api/prompts/`):

- In `logic_groups`, add your logic to the right group(s): `cgs_compatible`, `cost_based`, or `capacity_based`, and to `atl_like` if it uses coalition syntax like ATL.
- In `module_paths`, add an entry pointing to your algorithm module (e.g. `COTL: "model_checker.algorithms.explicit.COTL.COTL"`).
- In `descriptions`, add a block with `name`, `description`, `syntax`, and `examples` so the API and docs can describe the logic.

**logic_config.py** (in `workbench/api/services/model_checking/utils/`):

- If you reuse another parser, add your logic to `PARSER_MODULE_MAP` (see Step 1).
- If the API must extract agents from formulas (e.g. for AI or prompts), add an entry in `AGENT_EXTRACTION_CONFIG` (e.g. for COTL: coalition and cost bound, similar to OATL).

---

## Step 5: Tests and examples

**Integration test.** In `model_checker/tests/integration/interface/test_model_checker_api.py`:

- Add your logic to `LOGIC_CONFIG`: the checker function and the path to an example model as a tuple `(model_type_folder, logic_folder, filename)` (e.g. `"COTL": (cotl_check, ("costCGS", "COTL", "cotl_model.txt"))`).
- Add at least one parametrized row in `test_model_checking_exact_state_sets` with a formula and the expected state set for that model.
- Optionally add error cases in `test_model_checking_error_paths`.

**Example files.** Put examples under `workbench/api/examples/`. The workbench discovers examples automatically from this directory. Use the same layout as other logics: `examples/<model_type>/<Logic>/`. For each model file `<name>.txt`, add a `<name>_formula.txt` with at least one formula. Example models do not need to be complete (e.g. some states may have no outgoing transition); the checker does not require transition completeness.

---

## Example: COTL in short

1. **Parser:** No new parser. COTL reuses OATL. In `logic_config.py`, add `LogicType.COTL` to `PARSER_MODULE_MAP` -> `model_checker.parsers.formulas.OATL.parser`.
2. **Model:** costCGS exists. In `model_parser_factory.py`, add `"COTL"` to `COST_BASED_FORMULAS`.
3. **Algorithm:** Add `algorithms/explicit/COTL/COTL.py`. Implement `_core_cotl_checking(model_parser, formula)` using the costCGS instance from the runner, parse with the OATL parser, run the solver, return via `format_model_checking_result`. Expose `model_checking(formula, filename)` calling `execute_model_checking_with_parser(formula, filename, "COTL", _core_cotl_checking)`.
4. **API:** In `workbench/api/schemas/requests.py` add `COTL = "COTL"`. In `workbench/api/prompts/logic_config.yaml` add COTL to `logic_groups.cost_based` and `atl_like`, set `module_paths.COTL`, and add `descriptions.COTL`. In `logic_config.py` add the parser map and agent extraction for COTL.
5. **Tests and examples:** Add COTL to `LOGIC_CONFIG` in `test_model_checker_api.py` and at least one test row. Add `examples/costCGS/COTL/cotl_model.txt` and `cotl_model_formula.txt` at the repo root.

---

## Checklist

- [ ] **Parser:** New in `parsers/formulas/<Logic>/` and `_AVAILABLE_PARSERS`, or reuse via `PARSER_MODULE_MAP` in `logic_config.py`.
- [ ] **Algorithm:** `algorithms/explicit/<Logic>/` with a core function and `model_checking(formula, filename)` using `execute_model_checking_with_parser` and returning the standard dict.
- [ ] **Model type:** Logic added to `COST_BASED_FORMULAS` or `CAPACITY_BASED_FORMULAS` in `model_parser_factory.py` if needed; or new game structure implemented and wired in the factory.
- [ ] **Schema:** `LogicType` in `workbench/api/schemas/requests.py`.
- [ ] **logic_config.yaml:** `module_paths`, `logic_groups`, `descriptions`.
- [ ] **logic_config.py:** `PARSER_MODULE_MAP` and/or `AGENT_EXTRACTION_CONFIG` if needed.
- [ ] **Integration test:** Entry in `LOGIC_CONFIG` and at least one case in `test_model_checking_exact_state_sets`.
- [ ] **Examples:** At least one model file and one formula file under the repo root `examples/<model_type>/<Logic>/`.
