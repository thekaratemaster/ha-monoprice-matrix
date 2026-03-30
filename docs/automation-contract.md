# Automation Contract

## Domain

`monoprice_matrix`

## Stable entity IDs

- `select.monoprice_matrix_output_1`
- `select.monoprice_matrix_output_2`
- `select.monoprice_matrix_output_3`
- `select.monoprice_matrix_output_4`
- `select.monoprice_matrix_audio_set`

## Valid options

Output selects:
- `Input 1`
- `Input 2`
- `Input 3`
- `Input 4`

Audio set select:
- `A`
- `B`
- `C`
- `D`

## Automation surface

- use `select.select_option` to route outputs or set audio presets
- helper package `packages/monoprice_matrix_helpers.yaml` wraps these stable entity IDs

## Compatibility expectations

- entity IDs above are treated as public contract
- option labels above are treated as public contract
- any breaking change requires a migration note and helper package update
