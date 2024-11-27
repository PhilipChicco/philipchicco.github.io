#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Starting Jekyll site tests..."

# Test 1: Check if required gems are installed
echo -n "Checking required gems... "
if bundle check > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
    echo "Running bundle install..."
    bundle install
fi

# Test 2: Check Jekyll configuration
echo -n "Checking Jekyll configuration... "
if bundle exec jekyll doctor > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
    echo "Please check your _config.yml file"
fi

# Test 3: Build site
echo -n "Building site... "
if bundle exec jekyll build > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
    echo "Build failed. Check the build output for errors:"
    bundle exec jekyll build --trace
fi

# Test 4: Check for broken links
echo "Checking for broken internal links..."
bundle exec jekyll build 2>&1 | grep -i "warning\|error"

# Test 5: Check assets
echo -n "Checking required assets... "
required_files=(
    "assets/css/custom.css"
    "assets/css/style.css"
    "_layouts/default.html"
    "index.md"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Missing: $file${NC}"
        all_files_exist=false
    fi
done

if $all_files_exist; then
    echo -e "${GREEN}OK${NC}"
fi

# Start local server if all tests pass
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    echo "Starting local server..."
    bundle exec jekyll serve --livereload
else
    echo -e "\n${RED}Some tests failed. Please fix the issues before starting the server.${NC}"
    exit 1
fi