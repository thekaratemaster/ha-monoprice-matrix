# ha-monoprice-matrix

Home Assistant project for the Monoprice 4x4 HDBaseT 2.0 Matrix.

## Contents

- `custom_components/monoprice_matrix/` - the custom integration
- `packages/monoprice_matrix_helpers.yaml` - optional helper package for friendly routing controls
- `docs/automation-contract.md` - stable entity IDs, options, and helper-package guidance

## Installation

Integration:
Copy `custom_components/monoprice_matrix/` into your Home Assistant `custom_components/` directory, restart Home Assistant, then add the integration from Settings -> Devices & Services.

Optional helper package:
Copy `packages/monoprice_matrix_helpers.yaml` into your Home Assistant `packages/` directory if you want the helper-driven routing workflow.

## Notes

This repo keeps the integration and its companion helper package together because they are designed to evolve as one Monoprice project.
