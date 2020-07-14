# screenshot-memories
Screenshots represent memories just like photos. This script adds the necessary metadata to your screenshots, so you can handle them properly alongside digital photos, e.g. in photo albums.

## Necessary libraries
* Python 3 Standard Libraries
* [pyexiv2](https://launchpad.net/pyexiv2)

## Usage
    ./screenshot-memories.py [--dryrun] imagefile [imagefile ...]

`--dryrun` prevents changes to files

Files already containing XMP or Exif metadata (e.g. photos or from previous runs) are ignored on write.

### Examples
In bash, using globbing (`*`) makes bulk changes easy:

    screenshot-memories.py --dryrun screenshotdirectory/*png

Unknown and untested filetypes are ignored, so the following command is safe:

    screenshot-memories.py --dryrun screenshotdirectory/*

Write changes to files:

    screenshot-memories.py screenshotdirectory/*

## What metadata gets added?
Metadata is added in *Exif* and *XMP* formats.

* Timestamps as found in filename or file creation date
* Tag "Screenshot" is added to aid filtering in photo albums

## Contributions and improvment
Bugs, code and feedback are welcome.
