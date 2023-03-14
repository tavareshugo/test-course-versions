#!/bin/bash

# create appendix.md file
echo "
---
title: "Archive"
---

:::{.callout-tip}
#### Archived Versions

This page lists links to archived versions of these materials, which ran as a live course on the given date. 
We highly recommend that you refer to the latest version of the materials, however you can use these as a reference if you attended one of our past live courses. 
:::

" > archive.md

# download latest 4 releases
while read tag
do 
  # get remote URL
  url=$(git config --get remote.origin.url | sed 's/.*://' | sed 's/.git$//')
  url=$(echo "https://github.com/$url/archive/refs/tags/${tag}.zip")
  
  # create directory
  mkdir -p archive/${tag}
  
  # download, unzip and move to directory
  wget -O ${tag}.zip $url
  unzip -d archive/${tag}/ ${tag}.zip
  
  # add to archive.md file
  date=$(echo $tag | sed 's/v//' | sed 's/\./-/g')
  echo "* [${date}](archive/${tag}/index.html)" >> archive.md
  
done < <(grep -v "#" .github/releases.txt | head -n 5 | tail -n 4)

# add appendix to _quarto.yml
echo "
  appendices:
    - text: Archive
      href: archive.md" >> _quarto.yml