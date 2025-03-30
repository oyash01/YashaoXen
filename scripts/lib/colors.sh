#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Print functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}× $1${NC}"; }
print_info() { echo -e "${YELLOW}➜ $1${NC}"; }
print_header() { echo -e "${PURPLE}=== $1 ===${NC}"; } 