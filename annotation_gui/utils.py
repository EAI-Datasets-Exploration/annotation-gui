from pathlib import Path


def get_csv_files(
    folder_path: str,
):
    directory = Path(folder_path)
    return [str(file.resolve()) for file in directory.glob(".csv")]


def create_model_fp_dict(
    folder_path: str,
):
    directory = Path(folder_path)
    return {
        model.name: str(model.resolve())
        for model in directory.iterdir()
        if model.is_dir()
    }


def get_model_name(folder_path: str):
    fp = Path(folder_path)
    return fp.parents[1].name


def create_dataset_fp_dict(folder_path: str):
    directory = Path(folder_path)
    return {file.parent.name: str(file.resolve()) for file in directory.glob("*/*.csv")}
