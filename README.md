### WISE mutation frequency data uploader

Run this script by first installing and activating micromamba:

```
micromamba create -f environment.yaml
micromamba activate uploader
python scripts/upload_data.py --data-folder data/WISE --config-file config.yaml --organism ORGANISM
```

This script will submit all data in the data-folder under the assumption this is all data from the same organism, i.e. `influenza` or `rsv` (the organism is set using ORGANISM).


Commandline to filter the tsvs (as only one has all RSV-B and the other RSV-A data)
```
tsv-filter   --header --str-eq  2:RSV-A data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_412866.tsv > timeline_mutation_multiple_batches_EPI_ISL_412866_filtered.tsv

tsv-filter  --header --str-eq  2:RSV-B data/WISE-rsv/timeline_mutation_multiple_batches_EPI_ISL_1653999.tsv > timeline_mutation_multiple_batches_EPI_ISL_1653999_filtered.tsv
```