# ha-monoprice-matrix

Home Assistant integration for the Monoprice 4x4 HDBaseT 2.0 Matrix.

Current version: **1.0.4**

## Contents

- `custom_components/monoprice_matrix/` — the custom integration
- `packages/monoprice_matrix_helpers.yaml` — optional helper package for friendly routing controls
- `docs/automation-contract.md` — stable entity IDs, options, and helper-package guidance

## Installation

### HACS (recommended)

1. In Home Assistant, open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/thekaratemaster/ha-monoprice-matrix` as an **Integration**
3. Install "Monoprice 4x4 HDBaseT 2.0 Matrix" from HACS
4. Restart Home Assistant
5. Add the integration from Settings → Devices & Services → Add Integration → "Monoprice 4x4 HDBaseT 2.0 Matrix"

### Manual

1. Copy `custom_components/monoprice_matrix/` into your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Add the integration from Settings → Devices & Services → Add Integration → "Monoprice 4x4 HDBaseT 2.0 Matrix"

### Optional helper package

Copy `packages/monoprice_matrix_helpers.yaml` into your Home Assistant `packages/` directory for the helper-driven routing workflow.

## Configuration

The integration only needs the **IP address or hostname** of the matrix during setup. The host can be updated later via the integration's options flow (Settings → Devices & Services → configure).

## Entities

| Entity ID | Type | Description |
|---|---|---|
| `select.monoprice_matrix_output_1` | Select | Routes Output 1 to an input |
| `select.monoprice_matrix_output_2` | Select | Routes Output 2 to an input |
| `select.monoprice_matrix_output_3` | Select | Routes Output 3 to an input |
| `select.monoprice_matrix_output_4` | Select | Routes Output 4 to an input |
| `select.monoprice_matrix_audio_set` | Select | Selects active audio preset (A/B/C/D) |

Output selects accept: `Input 1`, `Input 2`, `Input 3`, `Input 4`

Audio set select accepts: `A`, `B`, `C`, `D`

Entity IDs are stable — they are enforced on setup and treated as a public contract. See [docs/automation-contract.md](docs/automation-contract.md) for details.

## Notes

This repo keeps the integration and its companion helper package together because they are designed to evolve as one Monoprice project.
