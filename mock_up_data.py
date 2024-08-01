import datetime as dt
import random
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd
from faker import Faker


def main() -> None:
    dir_path = Path(__file__).parent.joinpath("data").resolve()
    dir_path.mkdir(exist_ok=True, parents=True)
    bdf = BEADDataFaker(
        output_dir=dir_path,
        num_challengers=100,
        num_challenges=10000,
        num_cais=2500,
        random_seed=42,
    )
    bdf.generate_data()


class BEADDataFaker:
    def __init__(
        self,
        output_dir: Union[Path, str],
        num_challengers: int = 1000,
        num_challenges: int = 250000,
        num_cais: int = 25000,
        pct_cais_challenged: float = 15.0,
        pct_served: float = 50,
        pct_unserved: float = 25,
        remake_data: bool = False,
        random_seed: Optional[int] = None,
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.setup_output_dir()
        self.remake_data = remake_data
        if random_seed is None:
            random_seed = random.randint(0, 2**32 - 1)
        self.fake = Faker("en_us", seed=random_seed)
        self.random_seed = random_seed
        self.num_challengers = num_challengers
        self.num_challenges = num_challenges
        self.num_cais = num_cais
        self.num_cai_challenges = int((pct_cais_challenged * self.num_cais / 100) // 1)
        if pct_served > 100:
            raise ValueError(f"pct_served must be under 100%. Got {pct_served}")
        if pct_unserved > 100:
            raise ValueError(f"pct_unserved must be under 100%. Got {pct_unserved}")
        if pct_unserved + pct_served > 100:
            raise ValueError(
                "pct_served and pct_unserved must sum to at most 100%. "
                f"Got pct_served: {pct_served}, pct_unserved: {pct_unserved}"
            )
        self.pct_served = pct_served
        self.pct_unserved = pct_unserved
        self.pct_underserved = 100 - pct_served - pct_unserved

    def setup_output_dir(self) -> None:
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def _get_data(self, data_format: str, data_generator_func: Callable) -> pd.DataFrame:
        file_path = self.output_dir.joinpath(f"{data_format}.csv")
        if self.remake_data or not file_path.is_file():
            data_generator_func()
        data_format_df = pd.read_csv(file_path, dtype="str").fillna("")
        return data_format_df

    def generate_data(self) -> None:
        self.challengers_df = self._get_data("challengers", self._gen_challengers)
        self.challenges_df = self._get_data("challenges", self._gen_challenges)
        self.cai_df = self._get_data("cai", self._gen_cais)
        self.cai_challenges_df = self._get_data("cai_challenges", self._gen_cai_challenges)
        self.post_challenge_cai_df = self._get_data(
            "post_challenge_cai", self._gen_post_challenge_cais
        )
        self.post_challenge_locations_df = self._get_data(
            "post_challenge_locations", self._gen_post_challenge_locations
        )
        self.unserved_df = self._get_data("unserved", self._gen_unserved)
        self.underserved_df = self._get_data("underserved", self._gen_underserved)

    def _gen_challengers(self) -> None:
        records = []
        for _ in range(self.num_challengers):
            category = random.choice(["L", "T", "N", "B"])
            if category == "B":
                provider_id = random.randint(100000, 999999)
            else:
                provider_id = random.randint(100000, 999999) if random.choice([True, False]) else ""
            record = {
                "challenger": self.fake.uuid4(),
                "category": category,
                "organization": self.fake.company(),
                "webpage": self.fake.url(),
                "provider_id": provider_id,
                "contact_name": self.fake.name(),
                "contact_email": self.fake.email(),
                "contact_phone": self.fake.numerify(text="###-###-####"),
            }
            records.append(record)
        pd.DataFrame(records).to_csv(self.output_dir.joinpath("challengers.csv"), index=False)

    def _gen_challenges(self) -> None:
        all_challengers = self.challengers_df["challenger"].copy()

        records = []
        for _ in range(self.num_challenges):
            challenge = self.fake.uuid4()
            challenge_type = random.choice([*"ASLDTBEPNVFMXYZ"])
            challenger = random.choice(all_challengers)

            challenge_date = self.fake.date_between_dates(
                dt.datetime.strptime("2024-01-01", "%Y-%m-%d"),
                dt.datetime.strptime("2024-06-01", "%Y-%m-%d"),
            )
            rebuttal_date = ""
            if random.random() > 0.6:
                rebuttal_date = self.fake.date_between_dates(
                    challenge_date,
                    dt.datetime.strptime("2024-09-01", "%Y-%m-%d"),
                )
            if rebuttal_date == "":
                min_resolution_date = challenge_date
            else:
                min_resolution_date = rebuttal_date
                rebuttal_date = dt.datetime.strftime(rebuttal_date, "%Y-%m-%d")
            resolution_date = ""
            if random.random() > 0.15:
                resolution_date = dt.datetime.strftime(
                    self.fake.date_between_dates(
                        min_resolution_date,
                        dt.datetime.strptime("2024-12-01", "%Y-%m-%d"),
                    ),
                    "%Y-%m-%d",
                )
            disposition = ""
            if rebuttal_date == "":
                disposition = random.choice(["I", "N", "A", "M"])
            else:
                disposition = random.choice(["I", "A", "S", "R", "M"])
            provider_id = random.randint(100000, 999999)
            if challenge_type == "P" and random.random() > 0.6:
                provider_id = ""
            location_id = random.randint(10**9, 10**10 - 1)
            unit = ""
            if random.random() > 0.97:
                unit = self.fake.secondary_address().split()[1]
            technology = random.choice([10, 40, 50, 60, 61, 70, 71, 72, 0])
            if challenge_type == "N" and random.random() > 0.85:
                technology = ""
            reason_code = ""
            if challenge_type == "A":
                reason_code = random.choice([1, 2, 3, 4, 5, 6, 8, 9])
            evidence_file_id = self.fake.file_name(extension="pdf")
            if challenge_type in ["V", "E"] and random.random() > 0.85:
                evidence_file_id = ""
            response_file_id = ""
            if rebuttal_date != "":
                response_file_id = self.fake.file_name(extension="pdf")
            resolution = self.fake.text(50)
            if (
                challenge_type != "E" and disposition not in ["I", "R", "S"]
            ) and random.random() > 0.4:
                resolution = ""

            advertised_download_speed = random.randint(0, 1500)
            advertised_upload_speed = random.randint(0, 1500)
            if challenge_type == "N" and random.random() > 0.75:
                advertised_download_speed = ""
                advertised_upload_speed = ""
            download_speed = random.randint(0, 1500)
            upload_speed = random.randint(0, 1500)
            if challenge_type not in ["S", "M"] and random.random() > 0.9:
                download_speed = ""
                upload_speed = ""
            latency = random.uniform(3, 200)
            if challenge_type not in ["L", "M"] and random.random() > 0.9:
                latency = ""

            record = {
                "challenge": challenge,
                "challenge_type": challenge_type,
                "challenger": challenger,
                "challenge_date": challenge_date,
                "rebuttal_date": rebuttal_date,
                "resolution_date": resolution_date,
                "disposition": disposition,
                "provider_id": provider_id,
                "technology": technology,
                "location_id": location_id,
                "unit": unit,
                "reason_code": reason_code,
                "evidence_file_id": evidence_file_id,
                "response_file_id": response_file_id,
                "resolution": resolution,
                "advertised_download_speed": advertised_download_speed,
                "download_speed": download_speed,
                "advertised_upload_speed": advertised_upload_speed,
                "upload_speed": upload_speed,
                "latency": latency,
            }
            records.append(record)
        pd.DataFrame(records).to_csv(self.output_dir.joinpath("challenges.csv"), index=False)

    def _gen_cais(self) -> None:
        unique_entity_names = set()
        unique_entity_numbers = set("")
        while len(unique_entity_names) < self.num_cais:
            unique_entity_names.add(self.fake.unique.company())
        unique_entity_names = list(unique_entity_names)

        records = []
        for i in range(0, self.num_cais):
            cai_type = random.choice([*"SLGHFPC"])

            entity_number = ""
            if cai_type in ["S", "L"]:
                if random.random() >= 0.9:
                    while entity_number in unique_entity_numbers:
                        entity_number = str(random.randint(0, 10**7))
                    unique_entity_numbers.add(entity_number)

            cms_number = ""
            if cai_type in ["H"]:
                if random.random() < 0.5:
                    cms_number = str(random.randint(0, 10**6 - 1)).zfill(6)
                else:
                    cms_number = str(random.randint(0, 10**10 - 1)).zfill(10)

            frn = ""
            if cai_type in ["S", "L", "H"]:
                frn = str(random.randint(0, 10**10 - 1)).zfill(10)

            location_id = ""
            address_primary = ""
            city = ""
            state = self.fake.state_abbr(include_freely_associated_states=False)
            zip_code = ""
            longitude = ""
            latitude = ""
            location_roll = random.random()
            if 0 <= location_roll <= 0.333:
                location_id = str(random.randint(10**9, 10**10 - 1))
            elif 0.333 < location_roll <= 0.667:
                street_number = self.fake.building_number()
                street_name = self.fake.street_name()
                address_primary = f"{street_number} {street_name}"
                city = self.fake.city()
                zip_code = self.fake.zipcode_in_state(state)
            else:
                # NOTE: these probably won't be in the right state
                lat_long = self.fake.local_latlng()
                longitude = lat_long[1]
                latitude = lat_long[0]

            explanation = self.fake.text(60)
            if cai_type not in ["C", "R"] and random.random() > 0.8:
                explanation = ""
            need = 1000
            availability = 10 * random.randint(0, 150)

            record = {
                "type": cai_type,
                "entity_name": unique_entity_names[i],
                "entity_number": entity_number,
                "CMS number": cms_number,
                "frn": frn,
                "location_id": location_id,
                "address_primary": address_primary,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "longitude": longitude,
                "latitude": latitude,
                "explanation": explanation,
                "need": need,
                "availability": availability,
            }
            records.append(record)
        pd.DataFrame(records).to_csv(self.output_dir.joinpath("cai.csv"), index=False)

    def _gen_cai_challenges(self) -> None:
        cai_challengers = (
            self.challengers_df["challenger"]
            .sample(
                frac=0.1,
                replace=False,
                random_state=self.random_seed,
            )
            .to_list()
        )
        challenged_cais_df = self.cai_df.sample(
            n=self.num_cai_challenges,
            replace=True,
            ignore_index=True,
            random_state=self.random_seed,
        )

        records = []
        for _, cai_row in challenged_cais_df.iterrows():
            challenge = self.fake.uuid4()
            challenge_type = random.choice([*"CGQR"])
            challenger = random.choice(cai_challengers)
            if challenge_type == "C":
                category_code = random.choice([*"DNITO"])
            elif challenge_type == "R":
                category_code = random.choice([*"XBRDO"])
            else:
                category_code = random.choice([*"XBRDNITO"])
                if challenge_type != "G" and random.random() > 0.8:
                    category_code = ""
            disposition = random.choice([*"INASR"])
            challenge_explanation = self.fake.text(50)
            if challenge_type not in ["C", "R"] and random.random() > 0.8:
                challenge_explanation = ""

            record = {
                "challenge": challenge,
                "challenge_type": challenge_type,
                "challenger": challenger,
                "category_code": category_code,
                "disposition": disposition,
                "challenge_explanation": challenge_explanation,
                "type": cai_row["type"],
                "entity_name": cai_row["entity_name"],
                "entity_number": cai_row["entity_number"],
                "CMS number": cai_row["CMS number"],
                "frn": cai_row["frn"],
                "location_id": cai_row["location_id"],
                "address_primary": cai_row["address_primary"],
                "city": cai_row["city"],
                "state": cai_row["state"],
                "zip_code": cai_row["zip_code"],
                "longitude": cai_row["longitude"],
                "latitude": cai_row["latitude"],
                "explanation": cai_row["explanation"],
                "need": cai_row["need"],
                "availability": cai_row["availability"],
            }
            records.append(record)
        pd.DataFrame(records).to_csv(self.output_dir.joinpath("cai_challenges.csv"), index=False)

    def _gen_post_challenge_locations(self) -> None:
        """I just want some mocked up some data, so I'm not attempting to
        implement all of the eligibility and served/{un|under}served logic
        right now (maybe later though).
        """

        records = []
        for loc_id in self.challenges_df["location_id"].to_list():
            record = {
                "location_id": loc_id,
                "classification": random.choice([0, 1, 2]),
            }
            records.append(record)
        pd.DataFrame(records).to_csv(
            self.output_dir.joinpath("post_challenge_locations.csv"),
            index=False,
        )

    def _gen_post_challenge_cais(self) -> None:
        """I just want some mocked up some data. I put little thought into
        the correctness of this process beyond ensuring it produces
        an output matching the data model (ie right columns and order).
        """
        ineligible_cai_mask = self.cai_challenges_df["challenge_type"].isin(
            ["R", "Q"]
        ) & self.cai_challenges_df["disposition"].isin(["A", "S", "N"])
        affirmed_cai_mask = self.cai_challenges_df["challenge_type"].isin(
            ["C", "G"]
        ) & self.cai_challenges_df["disposition"].isin(["A", "S", "N"])
        cais_to_remove = (
            self.cai_challenges_df.loc[ineligible_cai_mask].copy().reset_index(drop=True)
        )
        cais_to_add_or_affirm = (
            self.cai_challenges_df.loc[affirmed_cai_mask].copy().reset_index(drop=True)
        )

        cai_id_cols = [
            "entity_name",
            "location_id",
            "address_primary",
            "city",
            "state",
            "zip_code",
            "longitude",
            "latitude",
        ]

        merged_cai_df = pd.merge(
            left=self.cai_df.copy(),
            right=cais_to_remove,
            how="left",
            on=cai_id_cols,
            suffixes=("", "_ineligible"),
        )
        merged_cai_df = (
            merged_cai_df.loc[merged_cai_df["type_ineligible"].isnull()]
            .copy()
            .reset_index(drop=True)
        )

        merged_cai_df = pd.concat(
            [
                merged_cai_df[self.cai_df.columns].copy(),
                cais_to_add_or_affirm[self.cai_df.columns].copy(),
            ]
        )
        eligible_cais_df = merged_cai_df.drop_duplicates(subset=cai_id_cols, ignore_index=True)
        eligible_cais_df.to_csv(self.output_dir.joinpath("post_challenge_cai.csv"), index=False)

    def _gen_unserved(self) -> None:
        self.post_challenge_locations_df.loc[
            self.post_challenge_locations_df["classification"] == "0",
            "location_id",
        ].to_csv(self.output_dir.joinpath("unserved.csv"), index=False, header=False)

    def _gen_underserved(self) -> None:
        self.post_challenge_locations_df.loc[
            self.post_challenge_locations_df["classification"] == "1",
            "location_id",
        ].to_csv(
            self.output_dir.joinpath("underserved.csv"),
            index=False,
            header=False,
        )


if __name__ == "__main__":
    main()
