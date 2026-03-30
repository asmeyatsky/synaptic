#!/bin/bash
pip3 install -e .
python3 -m uvicorn synaptic_bridge.presentation.api.main:app --reload
