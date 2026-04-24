"""Schema for external module manifests."""

from typing import List, Optional

from pydantic import BaseModel, Field


class LogicSection(BaseModel):
    name: str = Field(
        min_length=1,
        pattern=r"^[A-Z][A-Za-z0-9]*(?:_[A-Z][A-Za-z0-9]*)*$",
        description="Logic identifier in PascalCase (underscores allowed between Pascal segments), e.g. Wallet_ATL.",
    )
    model_type: str = Field(
        min_length=1,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
        description="Game-structure model type in CamelCase/PascalCase, e.g. costCGS, TimedCGS.",
    )


class ParserSection(BaseModel):
    module: str = Field(min_length=1)
    class_name: str = Field(
        min_length=1,
        pattern=r"^[A-Z][A-Za-z0-9]*(?:_[A-Z][A-Za-z0-9]*)*$",
    )


class CheckerSection(BaseModel):
    module: str = Field(min_length=1)
    entry_point: str = Field(min_length=1)


class GameStructureSection(BaseModel):
    """Bundle-resident game-structure parser (CGS-style) used for model files."""

    module: str = Field(
        min_length=1,
        description=(
            "Dotted import path from the bundle root, e.g. "
            "parsers.game_structures.cgs.cgs."
        ),
    )
    class_name: str = Field(
        min_length=1,
        pattern=r"^[A-Z][A-Za-z0-9]*(?:_[A-Z][A-Za-z0-9]*)*$",
        description="Python class name in PascalCase (underscores allowed between Pascal segments).",
    )
    integration_module: Optional[str] = Field(
        default=None,
        description=(
            "Import path after integration (default: model_checker.<module>). "
            "Use when the bundle path does not map 1:1 to the installed package."
        ),
    )


class ExampleItem(BaseModel):
    model: str = Field(min_length=1)
    formula: str = Field(min_length=1)
    expected_result: Optional[str] = None


class TestItem(BaseModel):
    path: str = Field(min_length=1)


class ExtraPathItem(BaseModel):
    """Additional directory trees to copy from the bundle into the target repo."""

    source: str = Field(
        min_length=1,
        description="Path relative to bundle root (posix-style), e.g. parsers/game_structures/cgs",
    )
    target: str = Field(
        min_length=1,
        description="Path relative to target repository root, e.g. model_checker/parsers/game_structures/cgs",
    )


class ModuleManifest(BaseModel):
    schema_version: Optional[str] = "1"
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1)
    logic: LogicSection
    parser: ParserSection
    checker: CheckerSection
    game_structure: Optional[GameStructureSection] = Field(
        default=None,
        description=(
            "Declare how to load the game-structure class from the bundle and, after integration, from the repo. "
            "When set, validation and integration wire this type without editing core model_factory by hand."
        ),
    )
    examples: List[ExampleItem] = []
    tests: List[TestItem] = []
    extra_paths: List[ExtraPathItem] = Field(
        default_factory=list,
        description="Extra directories/files to copy during integration (multi-file modules, game structures, etc.).",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Optional list of PEP 508 requirement strings.",
    )
