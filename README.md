
# OwensGeoMind

**Version:** 0.3.0 Beta  
**Author:** Antonio Owens  
**License:** GPL-3.0-or-later  
**Minimum QGIS Version:** 3.28

## Overview

OwensGeoMind is a QGIS plugin that combines local AI assistance,
GIS learning tools, geoprocessing workflows, and spatial data
quality checks.

The plugin is designed to help GIS users learn, inspect,
process, and validate spatial datasets.

## Features

### Local AI GIS Assistant
- Ask questions about GIS concepts and workflows.
- Receive explanations of buffers, clipping, CRS, and layers.
- Use a local Llama 3.2 model through Ollama.

### FieldProof Lite
- Run GIS data quality checks.
- Identify supported attribute and geometry issues.
- Export detected issues to CSV.
- Perform read-only checks without modifying source data.

### GIS Processing Tools
- Inspect project layers.
- Create buffers.
- Perform clipping operations.

### AI Setup Wizard
- Check the local Ollama connection.
- Open the official Ollama download page.
- Display model installation instructions.
- Check whether the required AI model is available.
- Continue using non-AI tools without Ollama.

## Requirements

- QGIS 3.28 or later.
- Python and PyQGIS supplied by QGIS.
- Ollama and the llama3.2 model for AI functionality.

Ollama is optional for FieldProof Lite and non-AI GIS tools.

## Installation

1. Download the OwensGeoMind plugin ZIP.
2. Open QGIS.
3. Select Plugins > Manage and Install Plugins.
4. Select Install from ZIP.
5. Choose the OwensGeoMind ZIP file.
6. Install and enable the plugin.
7. Open OwensGeoMind from the Plugins menu.

## Setting Up Local AI

1. Download Ollama from https://ollama.com/download
2. Install and start Ollama.
3. Open Terminal or PowerShell.
4. Run:

    ollama pull llama3.2

5. Open OwensGeoMind inside QGIS.
6. Click AI Setup - Ollama.
7. Click Check Ollama to verify the connection.

The AI model runs locally. AI-generated explanations may
contain errors and should be verified before use.

## Privacy

The AI assistant communicates with a locally running
Ollama service at http://127.0.0.1:11434.

Users should review Ollama's configuration and any
models they install before processing sensitive data.

## License

Copyright (C) 2026 Antonio Owens

Licensed under GNU GPL-3.0-or-later.

See LICENSE and COPYRIGHT for details.
