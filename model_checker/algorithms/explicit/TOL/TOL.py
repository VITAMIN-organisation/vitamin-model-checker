from .tol_model_checking import model_checking_ast as model_checking


def verify(formula: str, model_path: str):
    return model_checking(formula, model_path)
