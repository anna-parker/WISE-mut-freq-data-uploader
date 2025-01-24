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

This script submits all data in the `data-folder` under the assumption this is all data from the same `organism`, i.e. `influenza` or `rsv`.

This script assumes that all data that you submit in the data-folder is from the same organism and that (date, location, reference) pairs are unique, even if they are split up among files. Please check that this is true before running this script. 

Note that for RSV `submissionId`s were duplicated across files, as all RSV-B sequences and RSV-A sequences were in both files, but each file only had the results of one assay. Thus, the empty duplications, i.e. RSV-B sequences in the RSV-A results file had to be removed before running the script. I did this using the commands: 

```
tsv-filter   --header --str-eq  2:RSV-A data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_412866.tsv > timeline_mutation_multiple_batches_EPI_ISL_412866_filtered.tsv

tsv-filter  --header --str-eq  2:RSV-B data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_1653999.tsv > timeline_mutation_multiple_batches_EPI_ISL_1653999_filtered.tsv
```