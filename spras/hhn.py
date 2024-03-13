from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.dataset import Dataset
from spras.util import add_rank_column
from spras.interactome import (
    reinsert_direction_col_undirected,
)
from spras.prm import PRM

__all__ = ['HHN']


"""
Hierarchical HotNet will cluster high-weight nodes that are topologically close to ID statistically significant subnetworks.

Expected raw input format:
    - need Index-to-gene file:
        ID1 Gene1
    - need Edge List (network) file:
        ID1 ID2
    - need Gene-to-score file (prizes):
        Gene1 Weight
"""
class HHN(PRM):
    required_inputs = ['scores', 'edge_list', 'index']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in HHN.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            # NODEID is always included in the node table
            node_df = data.request_node_columns(['prize'])
        # elif data.contains_node_columns(['sources', 'targets']):
        #     # If there aren't prizes but are sources and targets, make prizes based on them
        #     node_df = data.request_node_columns(['sources','targets'])
        #     node_df.loc[node_df['sources']==True, 'prize'] = 1.0
        #     node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise ValueError("HHN requires node prizes")

        # Create the HHN Gene-to-score file 
        # NOTE: May need to add warning
        node_df.to_csv(filename_map['scores'],sep='\t',index=False,columns=['NODEID','prize'],header=None)

        # Create Index-to-gene file

        # get network file
        edges_df = data.get_interactome()
        edges_df.columns = ['NODEID1', 'NODEID2', 'Weight', 'Direction']
        edges_df = edges_df[['NODEID1', 'NODEID2']]

        # get unique node values
        combined_nodes = pd.concat([edges_df['NODEID1'], edges_df['NODEID2']]).unique()
        
        # create Index-to-gene file
        index_df = pd.DataFrame({'NODEID': combined_nodes})
        index_df['Index'] = range(1, len(index_df) + 1)
        index_df.to_csv(filename_map['index'], sep='\t',index=False,columns=['Index', 'NODEID'],header=None)

        # create merged network file for edge list
        merged_df = edges_df.merge(index_df, left_on='NODEID1', right_on='NODEID')\
        .merge(index_df, left_on='NODEID2', right_on='NODEID', suffixes=('_1', '_2'))[['Index_1', 'Index_2']]

        # Save to edge list file without headers
        merged_df.to_csv(filename_map['edge_list'], sep='\t', index=False, columns=['Index_1', 'Index_2'], header=None)


    # TODO add parameter validation
    # TODO add support for knockout argument
    # TODO add reasonable default values
    # TODO document required arguments
    @staticmethod
    def run(scores=None, edge_list=None, index=None, output_file=None, container_framework="docker"):
        """
        Run HHN with Docker
        @param scores:  input Gene-to-score/prizes file (required) 
        @param edge_list:  input network file (required)
        @param index: input Index-to-gene file (required)
        @param output_file: path to the output pathway file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        # Add additional parameter validation
        # Could consider setting the default here instead
        if not scores or not edge_list or not index or not output_file:
            raise ValueError('Required Hierarchical HotNet arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, scores_file = prepare_volume(scores, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(edge_list, work_dir)
        volumes.append(bind_path)

        bind_path, index_file = prepare_volume(index, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # HHN requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/hhn-results.txt'  # Use posix path inside the container

        command = ['bash',
                   '/HHN/hhn.sh',
                   "-s", scores_file,
                   "-e", edges_file,
                   "-i", index_file,
                   "-o", mapped_out_prefix]


        print('Running Hierarchical HotNet with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "hhn"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        output_edges = Path(next(out_dir.glob('hhn-results.txt')))
        output_edges.rename(output_file)


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Raw format is node1 node2 with no header
        df = pd.read_csv(raw_pathway_file, sep='\t', header=None)
        df = add_rank_column(df)
        df = reinsert_direction_col_undirected(df)

        df.to_csv(standardized_pathway_file, header=False, index=False,
                  sep='\t')