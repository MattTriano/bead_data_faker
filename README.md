# BEAD Challenge Testing Data Generator

This code generates datasets for testing and demonstrating the [UChicago BEAD Challenge Data Validation package](https://github.com/uchicago-dsi/uchicago-bead-challenge-validation-tool).

The `mock_up_data.py` script generates fake data that complies with (nearly) all of the specifications in the [BEAD Challenge Policy Notice](https://www.ntia.gov/sites/default/files/2023-11/bead_challenge_process_policy_notice.pdf#page=23).

The `deface_bead_data.py` script loads those data files, introduces defects into some of the data files, and outputs the damaged data into another directory.

## Setup

Note: There are many ways to do python environment management. This example uses python's build in `venv` module but any env mgmt tool would also work.

From a command line, first navigate to wherever you want, clone the repo, and enter that clone dir

```console
cd /path/to/wherever && git clone git@github.com:MattTriano/bead_data_faker.git
cd bead_data_faker
```

Then create a `venv` and install requirements
```
python -m venv your_venv
source your_venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs required packages into the `your_venv` dir. The main packages are:
* `pandas` (for data input, output, and manipulation),
* `Faker` (for mocking up reasonable data), and
* `bead_inspector`


## Usage

Mock up some fake data with the `mock_up_data.py` (outputs to `<file_dir>/data/`) then run `deface_bead_data.py` to load that data, introduce defects, and output the defective data to `<file_dir>/bad_data/`.

```console
python mock_up_data.py
python deface_bead_data.py
```

Now that both data and defective-data is available, you can use the `bead_inspector` tool to produce reports showing the detected issues

```console
bead_inspector data/
bead_inspector bad_data/
```

The reports will generate in `data/reports/` and `bad_data/reports/` respectively. Open one or both of the reports; they should open in your browser.


# Cleanup

If you followed the example code in this README (i.e., if you used a `venv` for environment management), you can completely uninstall everything by simply deleting the `bead_data_faker` folder.

