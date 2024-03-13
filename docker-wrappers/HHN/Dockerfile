# Hierarchical HotNet wrapper
# https://github.com/raphael-group/hierarchical-hotnet
# Activates the conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3:4.9.2

# Need to install fortran compiler
RUN apt-get -qq update --allow-releaseinfo-change && \
    apt-get install -y gfortran && \
    rm -rf /var/lib/apt/lists/*
    
RUN commit=2568ae14363a14bc43113d7f21775280a3b7d924 && \
    wget https://github.com/oliverfanderson/hierarchical-hotnet/tarball/$commit && \
    tar -zxvf $commit && \
    rm $commit && \
    mv oliverfanderson-hierarchical-hotnet-* HHN

WORKDIR /HHN

COPY environment.yml .
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "hhn", "/bin/bash", "-c"]

# Activate Conda environment and set ENTRYPOINT
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "hhn"]