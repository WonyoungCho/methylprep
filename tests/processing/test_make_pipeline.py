import sys
import numpy as np
import pandas as pd
from pathlib import Path
import shutil
# App
from methylprep.processing import pipeline
from methylprep.utils.files import download_file
#patching
try:
    # python 3.4+ should use builtin unittest.mock not mock package
    from unittest.mock import patch
except ImportError:
    from mock import patch


class TestMakePipeline():
    test_data_dir = 'docs/example_data/GSE69852'

    def clean_dir(self, other_dir=None):
        test_data_dir = self.test_data_dir if other_dir == None else other_dir
        test_outputs = [
            Path(test_data_dir, 'control_probes.pkl'),
            Path(test_data_dir, 'beta_values.pkl'),
            Path(test_data_dir, 'm_values.pkl'),
            Path(test_data_dir, 'meth_values.pkl'),
            Path(test_data_dir, 'unmeth_values.pkl'),
            Path(test_data_dir, 'noob_meth_values.pkl'),
            Path(test_data_dir, 'noob_unmeth_values.pkl'),
            Path(test_data_dir, 'sample_sheet_meta_data.pkl'),
            Path(test_data_dir, 'poobah_values.pkl'),
            Path(test_data_dir, '9247377085', '9247377085_R04C02_processed.csv'),
            Path(test_data_dir, '9247377093', '9247377093_R02C01_processed.csv'),
            ]
        for outfile in test_outputs:
            if outfile.exists():
                outfile.unlink()

    def test_make_pipeline_sesame_steps_vs_all(self):
        """
        - check that we get back useful data.
        - compare sesame=True with a list of equivalent steps
        check that output files exist, then remove them."""
        self.clean_dir()
        alt_data_dir = 'docs/example_data/GSE69852_alt'
        copy_files = [
            '9247377093_R02C01_Red.idat',
            '9247377093_R02C01_Grn.idat',
            '9247377085_R04C02_Red.idat',
            '9247377085_R04C02_Grn.idat',
            'samplesheet.csv']

        if not Path(alt_data_dir).exists():
            Path(alt_data_dir).mkdir()
        for copy_file in copy_files:
            if not Path(alt_data_dir,copy_file).exists():
                shutil.copy(Path(self.test_data_dir, copy_file), Path(alt_data_dir, copy_file))

        df1 = pipeline.make_pipeline(self.test_data_dir,
            steps=['all'],
            exports=['all'],
            estimator='betas')

        df2 = pipeline.make_pipeline(alt_data_dir,
            steps=['infer_channel_switch', 'poobah', 'quality_mask', 'noob', 'dye_bias'],
            exports=['all'],
            estimator='betas')

        test_outputs = [
            'control_probes.pkl',
            'beta_values.pkl',
            'meth_values.pkl',
            'unmeth_values.pkl',
            'noob_meth_values.pkl',
            'noob_unmeth_values.pkl',
            'sample_sheet_meta_data.pkl',
            'poobah_values.pkl',
            Path('9247377085', '9247377085_R04C02_processed.csv'),
            Path('9247377093', '9247377093_R02C01_processed.csv'),
            ]

        assert df1.equals(df2)

        # verify outputs all exist
        for outfile in test_outputs:
            filepath = Path(self.test_data_dir, outfile)
            if not filepath.exists():
                raise FileNotFoundError(f"Expected {filepath.name} to be generated by run_pipeline() but it was missing.")
            else:
                print('+', outfile)
                #outfile.unlink()
        for outfile in test_outputs:
            filepath = Path(alt_data_dir, outfile)
            if not filepath.exists():
                raise FileNotFoundError(f"Expected {filepath.name} to be generated by run_pipeline() but it was missing.")
            else:
                print('+', outfile)
                #outfile.unlink()

        # compare output files to ensure they match each other
        for outfile in test_outputs:
            filepath1 = Path(self.test_data_dir, outfile)
            filepath2 = Path(alt_data_dir, outfile)
            if filepath1.suffix in ('.pkl','.csv'):
                if filepath1.suffix == '.pkl':
                    df1 = pd.read_pickle(filepath1)
                    df2 = pd.read_pickle(filepath2)
                elif filepath1.suffix == '.csv':
                    df1 = pd.read_csv(filepath1)
                    df2 = pd.read_csv(filepath2)
                if isinstance(df1, pd.DataFrame) and isinstance(df2, pd.DataFrame):
                    assert df1.equals(df2)
                    print(f"{outfile}: df1 equals df2: {df1.equals(df2)}")
                elif isinstance(df1, dict) and isinstance(df2, dict):
                    # control, mouse probes are dict of dataframes; assume save length
                    for i in range(len(df1)):
                        dfa = list(df1.values())[i]
                        dfb = list(df2.values())[i]
                        assert dfa.equals(dfb)
                        print(f"{outfile}, sample[{i}]: df1 equals df2: {dfa.equals(dfb)}")
                else:
                    raise ValueError("unknown/mismatched output")

        # match run_pipeline to make_pipeline for basic sesame
        shutil.rmtree(Path(alt_data_dir))
        if not Path(alt_data_dir).exists():
            Path(alt_data_dir).mkdir()
        for copy_file in copy_files:
            if not Path(alt_data_dir,copy_file).exists():
                shutil.copy(Path(self.test_data_dir, copy_file), Path(alt_data_dir, copy_file))

        df2 = pipeline.run_pipeline(alt_data_dir,
            sesame=True,
            betas=True,
            poobah=True, # sesame sets this
            export_poobah=True,
            save_uncorrected=True,
            save_control=True,
            export=True, #CSV
            )

        # compare output files to ensure they match each other
        # passes: control, meth, unmeth
        failed = []
        for outfile in test_outputs:
            filepath1 = Path(self.test_data_dir, outfile)
            filepath2 = Path(alt_data_dir, outfile)
            if filepath1.suffix in ('.pkl','.csv'):
                if filepath1.suffix == '.pkl':
                    df1 = pd.read_pickle(filepath1)
                    df2 = pd.read_pickle(filepath2)
                elif filepath1.suffix == '.csv':
                    df1 = pd.read_csv(filepath1)
                    df2 = pd.read_csv(filepath2)
                if isinstance(df1, pd.DataFrame) and isinstance(df2, pd.DataFrame):
                    if not df1.equals(df2):
                        failed.append(f"{outfile} FAILED to match {df1.equals(df2)}")
                    else:
                        print(f"{outfile}: df1 equals df2: {df1.equals(df2)}")
                elif isinstance(df1, dict) and isinstance(df2, dict):
                    # control, mouse probes are dict of dataframes; assume save length
                    for i in range(len(df1)):
                        dfa = list(df1.values())[i]
                        dfb = list(df2.values())[i]
                        assert dfa.equals(dfb)
                        print(f"run vs make pipeline: {outfile}, sample[{i}]: df1 equals df2: {dfa.equals(dfb)}")
                else:
                    raise ValueError("unknown/mismatched output")
        # reset
        shutil.rmtree(Path(alt_data_dir))
        self.clean_dir()

        if failed:
            for test in failed:
                print(test)
            raise AssertionError("One or more tests failed")


    @staticmethod
    def __test_make_pipeline_extra__(): # could test no_dye_no_noob
        """ check that we get back useful data.
        check that output files exist, then remove them."""
        # partial lists, m_value output, run_pipeline matches make_pipeline
        test_data_dir = 'docs/example_data/GSE69852'
        test_outputs = [
            Path(test_data_dir, 'control_probes.pkl'),
            Path(test_data_dir, 'beta_values.pkl'),
            # Path(test_data_dir, 'm_values.pkl'),
            Path(test_data_dir, 'meth_values.pkl'),
            Path(test_data_dir, 'unmeth_values.pkl'),
            Path(test_data_dir, 'noob_meth_values.pkl'),
            Path(test_data_dir, 'noob_unmeth_values.pkl'),
            Path(test_data_dir, 'sample_sheet_meta_data.pkl'),
            Path(test_data_dir, 'poobah_values.pkl'),
            Path(test_data_dir, '9247377085', '9247377085_R04C02_processed.csv'),
            Path(test_data_dir, '9247377093', '9247377093_R02C01_processed.csv'),
            ]
        for outfile in test_outputs:
            if outfile.exists():
                outfile.unlink()

        beta_df = pipeline.make_pipeline(test_data_dir,
            steps=['all'],
            exports=['all'],
            estimator='betas')
        for outfile in test_outputs:
            if not outfile.exists():
                raise FileNotFoundError(f"Expected {outfile.name} to be generated by run_pipeline() but it was missing.")
            else:
                print('+', outfile)
                outfile.unlink()
