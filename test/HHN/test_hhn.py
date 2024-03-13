import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.hhn import HHN

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/HHN/'
OUT_FILE = TEST_DIR+'output/sample-hhn-results.txt'


class TestHHN:
    """
    Run HHN tests in the Docker image
    """
    def test_hhn_required(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        HHN.run(
            scores=TEST_DIR+'input/sample-hhn-scores.txt',
            edge_list=TEST_DIR+'input/sample-hhn-edges.txt',
            index=TEST_DIR+'input/sample-hhn-index.txt',
            output_file=OUT_FILE
        )
        assert out_path.exists()

    def test_hhn_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No index
            HHN.run(
                scores=TEST_DIR+'input/sample-hhn-scores.txt',
                edge_list=TEST_DIR+'input/sample-hhn-edges.txt',
                output_file=OUT_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    # @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    # def test_pathlinker_singularity(self):
    #     out_path = Path(OUT_FILE)
    #     out_path.unlink(missing_ok=True)
    #     # Only include required arguments and run with Singularity
    #     HHN.run(
    #         scores=TEST_DIR+'input/sample-hhn-scores.txt',
    #         edge_list=TEST_DIR+'input/sample-hhn-edges.txt',
    #         index=TEST_DIR+'input/sample-hhn-index.txt',
    #         output_file=OUT_FILE,
    #         container_framework="singularity")
    #     assert out_path.exists()
