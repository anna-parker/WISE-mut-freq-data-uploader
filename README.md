### WISE mutation frequency data uploader

Run this script by first installing and activating [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html):

```
micromamba create -f environment.yaml
micromamba activate uploader
```

You then need to add your password and username to the `config.yaml` to submit sequences - by default this script submits to group 1 (WISE) but this can be altered in the config.

```
python scripts/upload_data.py --data-folder {PATH} --config-file config.yaml --organism {ORGANISM}
```

All metadata from the same organism should be kept in the same `data-folder`, `organism`, can take values `influenza` or `rsv`.

#### WARNING!! This script assumes that (date, location, reference) pairs are unique, even if they are split up among files - but it doesn't verify this! Please check that this is true before running this script. 

For example, for RSV `submissionId`s were duplicated across files. Each RSV-B and RSV-A sample was in both files, but each file only had mutations to one reference, i.e. only mutations from RSV-B or RSV-A. Thus, the empty duplications, i.e. RSV-B sequences in the RSV-A results file had to be removed before running the script. I did this using the commands: 

```
tsv-filter   --header --str-eq  2:RSV-A data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_412866.tsv > timeline_mutation_multiple_batches_EPI_ISL_412866_filtered.tsv

tsv-filter  --header --str-eq  2:RSV-B data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_1653999.tsv > timeline_mutation_multiple_batches_EPI_ISL_1653999_filtered.tsv
```