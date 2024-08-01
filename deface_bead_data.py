from pathlib import Path
import random

from faker import Faker
import pandas as pd


def main():
    DATA_DIR = Path("data").resolve()
    DEFECTIVE_DATA_DIR = Path("bad_data").resolve()
    DEFECTIVE_DATA_DIR.mkdir(exist_ok=True)
    challenge_breaker = ChallengesDefectMaker(DATA_DIR, DEFECTIVE_DATA_DIR)
    challenger_breaker = ChallengerDefectMaker(DATA_DIR, DEFECTIVE_DATA_DIR)


class ChallengesDefectMaker:
    def __init__(self, data_dir: Path, defective_dir: Path, seed: int = 42):
        self.data_dir = data_dir
        self.file_path = self.data_dir.joinpath("challenges.csv")
        self.defective_dir = defective_dir
        self.df = pd.read_csv(self.file_path, dtype=str).fillna("")
        self.seed = seed
        self.rng = self._random_number_generator()
        self.make_defective_data()
        self.output_bad_data()

    def _random_number_generator(self):
        random.seed(self.seed)
        while True:
            yield random.randint(1, (len(self.df) * 0.2) // 1)

    def get_n(self):
        return next(self.rng)

    def output_bad_data(self):
        output_file_path = self.defective_dir.joinpath(self.file_path.name)
        if not output_file_path.is_file():
            self.df.to_csv(output_file_path, index=False)
        else:
            print(f"Already a file in location {output_file_path}")

    def make_defective_data(self):
        self.make_data_breaking_rebuttal_file_and_date_rules()
        self.misorder_challenge_and_rebuttal_dates()
        self.misorder_challenge_and_resolution_dates()
        self.make_required_resolutions_null()
        self.make_required_technologies_null_or_defective()
        self.make_required_reason_code_defective_or_null()
        self.make_bad_provider_ids()

    def make_data_breaking_rebuttal_file_and_date_rules(self):
        rd_n = self.get_n()
        rd_mask = self.df["rebuttal_date"] == ""
        index_mask = self.df.loc[rd_mask].copy().sample(n=rd_n, random_state=rd_n).index
        self.df.loc[index_mask, "response_file_id"] = [
            random.choice(["a.pdf", "b.zip", "c.pdf d.pdf", "e.pdf"]) for i in range(rd_n)
        ]
        rf_n = self.get_n()
        rf_mask = (
            self.df.loc[self.df["response_file_id"].notnull()]
            .copy()
            .sample(n=rf_n, random_state=rf_n)
            .index
        )
        self.df.loc[rf_mask, "rebuttal_date"] = ""

    def misorder_challenge_and_rebuttal_dates(self):
        n = self.get_n()
        mask = self.df.sample(n=n, random_state=n).index
        challenge_dates = self.df.loc[mask, "challenge_date"].copy()
        self.df.loc[mask, "challenge_date"] = self.df.loc[mask, "rebuttal_date"]
        self.df.loc[mask, "rebuttal_date"] = challenge_dates

    def misorder_challenge_and_resolution_dates(self):
        n = self.get_n()
        mask = self.df.sample(n=n, random_state=n).index
        challenge_dates = self.df.loc[mask, "challenge_date"].copy()
        self.df.loc[mask, "challenge_date"] = self.df.loc[mask, "resolution_date"]
        self.df.loc[mask, "resolution_date"] = challenge_dates

    def make_required_resolutions_null(self):
        n = self.get_n()
        mask = (self.df["disposition"].isin(["I", "R", "S"])) | (self.df["challenge_type"] == "E")
        index_mask = self.df.loc[mask].sample(n=n, random_state=n).index
        self.df.loc[index_mask, "resolution"] = ""

    def make_required_technologies_null_or_defective(self):
        n = self.get_n()
        mask = self.df["challenge_type"] != "N"
        index_mask = self.df.loc[mask].sample(n=n, random_state=n).index
        self.df.loc[index_mask, "technology"] = ""

    def make_required_reason_code_defective_or_null(self):
        n = self.get_n()
        mask = self.df["challenge_type"] == "A"
        index_mask = self.df.loc[mask].sample(n=n, random_state=n).index
        self.df.loc[index_mask, "reason_code"] = [random.choice(["7", "0", "A"]) for i in range(n)]

    def make_bad_provider_ids(self):
        n = self.get_n()
        mask = self.df.sample(n=n, random_state=n).index
        self.df.loc[mask, "provider_id"] = [
            random.choice([random.randint(0, 999999), random.randint(1000000, 100000000)])
            for i in range(n)
        ]


class ChallengerDefectMaker:
    def __init__(self, data_dir: Path, defective_dir: Path, seed: int = 42):
        self.data_dir = data_dir
        self.file_path = self.data_dir.joinpath("challengers.csv")
        self.defective_dir = defective_dir
        self.df = pd.read_csv(self.file_path, dtype=str).fillna("")
        self.seed = seed
        self.rng = self._random_number_generator()
        self.fake = Faker()
        self.make_defective_data()
        self.output_bad_data()

    def _random_number_generator(self):
        random.seed(self.seed)
        while True:
            yield random.randint(4, ((len(self.df) * 0.2) + 5) // 1)

    def get_n(self):
        return next(self.rng)

    def output_bad_data(self):
        output_file_path = self.defective_dir.joinpath(self.file_path.name)
        if not output_file_path.is_file():
            self.df.to_csv(output_file_path, index=False)
        else:
            print(f"Already a file in location {output_file_path}")

    def make_defective_data(self):
        self.deface_challenger_ids()
        self.deface_webpages()

    def deface_challenger_ids(self):
        n = self.get_n()
        challenger_ids = set(self.df["challenger"].unique())
        new_challenger_ids = []
        while len(new_challenger_ids) < n:
            new_challenger_id = self.fake.pystr(min_chars=0, max_chars=100)
            if (
                new_challenger_id not in challenger_ids
                and new_challenger_id not in new_challenger_ids
            ):
                new_challenger_ids.append(new_challenger_id)
        mask = self.df.sample(n=n, random_state=n).index
        self.df.loc[mask, "challenger"] = new_challenger_ids

    def deface_webpages(self):
        n = self.get_n()
        mask = self.df["webpage"] != ""
        self.df.loc[mask, "webpage"] = self.df.loc[mask, "webpage"].str.replace("https://", "www.")
        self.df.loc[mask, "webpage"] = self.df.loc[mask, "webpage"].str.replace("http://", "ftp://")


if __name__ == "__main__":
    main()
