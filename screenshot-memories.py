#!/usr/bin/python3

# Copyright 2019 Florian Gruber
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import imghdr
import pyexiv2
import os
import re
import sys

"""Screenshots represent Memories.
This little Python module adds metadata to various screenshot types,
making it possible to handle them properly alongside digital photos,
e.g. in photo albums."""
# TODO: look up docstring conventions and reformat.


class Error(Exception):
  """Base class for exceptions in this module."""
  pass

class InsufficientMetadataError(Error):
  """Raised when essential metadata is missing."""

  def __init__(self, message):
    self.message = message

class UnsupportedFileTypeError(Error):
  """Raised when the format of the screenshot file is unknown or untested."""

  def __init__(self, message):
    self.message = message


def choose_best_datetime(fileinfo):
  """Returns the earliest valid timestamp from fileinfo."""
  valid_times = {}
  maxtime = datetime.datetime.now()
  maxtime_utc = datetime.datetime.utcnow()
  mintime = datetime.datetime(1990, 1, 1)
  for name in fileinfo:
    if "time" in name.lower() or "date" in name.lower():
      time = fileinfo[name]
      # sanity check datetime values, accounting for different timezones
      if time > mintime and (time < maxtime or time < maxtime_utc):
        valid_times[name] = time
      else:
        pass
  if not valid_times:
    raise InsufficientMetadataError("No valid timestamps found.")

  # choose earliest valid date in a generic way
  best = sorted(valid_times.values())[0]
  return best


def _find_datetime_metadata_fields(filepath, date_fragment):
  """For testing and debugging: Find all date fields in existing metadata.
  Returns a dict of those fields with their raw values as encountered."""
  md = pyexiv2.ImageMetadata(filepath)
  md.read()
  datefields = {}
  to_read = md.exif_keys + md.xmp_keys
  for fieldname in to_read:
    try:
      rv = md[fieldname].raw_value
      if date_fragment in rv:
        datefields[fieldname] = rv
    except KeyError:
      pass

  # TODO: pretty format print statements, e.g. with "," instead of "+"
  print("Date fields are: " + str(sorted(datefields.keys())))

  for k in sorted(datefields.keys()):
    v = datefields[k]
    print(v + "\t in \t" + k)

    # produces e.g. for a file edited in Shotwell:
    #   2019:09:13 11:00:07	 in 	Exif.Image.DateTime
    #   2019:09:13 11:00:07	 in 	Exif.Photo.DateTimeDigitized
    #   2019:09:13 11:00:07	 in 	Exif.Photo.DateTimeOriginal
    #   2019-09-13T09:00:07Z	 in 	Xmp.exif.DateTimeDigitized
    #   2019-09-13T09:00:07Z	 in 	Xmp.exif.DateTimeOriginal
    #   2019-09-13T09:00:07Z	 in 	Xmp.xmp.CreateDate

    # output from a file as written by this script with pyexiv2:
    #   2016:06:23 16:42:03	 in 	Exif.Image.DateTime
    #   2016:06:23 16:42:03	 in 	Exif.Photo.DateTimeDigitized
    #   2016:06:23 16:42:03	 in 	Exif.Photo.DateTimeOriginal
    #   2016-06-23T16:42:03.548402Z	 in 	Xmp.exif.DateTimeDigitized
    #   2016-06-23T16:42:03.548402Z	 in 	Xmp.exif.DateTimeOriginal
    #   2016-06-23T16:42:03.548402Z	 in 	Xmp.xmp.CreateDate

  sys.exit()
  return datefields


def guess_time_from_filepath(filepath):
  """Takes an educated guess when file was created based on filename and path.
  Returns an ISO datetime string."""
  # examples for valid datetime fragments in file path:
  #   1997-08-29T02:14:00
  #   2016-06-23_16-41-53
  #   2017-03-13-192338
  #   20190815-073404
  pattern = r"(\d{4})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})"
  match = re.search(pattern, filepath)
  guessed_datetime = None
  if match:
    # currently using naive date and time
    # timezone might be useful, maybe pass as command line parameter
    # ValueError is thrown if datetimes are out of range
    try:
      guessed_datetime = datetime.datetime(
        int(match.group(1)), # year
        int(match.group(2)), # month
        int(match.group(3)), # day
        hour=int(match.group(4)),
        minute=int(match.group(5)),
        second=int(match.group(6)) )
    except ValueError as e:
      pass

    # uncomment for metadata format testing only:
    #_find_datetime_metadata_fields(filepath, match.group(1))
  return guessed_datetime


def gather_file_info(filepath):
  """Tries to get info about a given file from filename and (some) metadata
  and returns them as a dictionary. Keys containing the substring "time"
  are used for datetime objects. Those objects are currently "naive",
  e.g. don't take timezone into account.
  Note that analyzing an untestet fileformat raises an exception."""
  fileinfo = {}
  fileinfo["path"] = filepath

  fileinfo["type"] = imghdr.what(filepath)
  if fileinfo["type"] not in ["jpeg", "png"]:
    raise UnsupportedFileTypeError("Untested file format " + str(fileinfo["type"]) + ".")

  if guess_time_from_filepath(filepath):
    fileinfo["pathtime_obj"] = guess_time_from_filepath(filepath)

  #ctime = os.path.getctime(filepath)
  mtime = os.path.getmtime(filepath)
  mtime_obj = datetime.datetime.fromtimestamp(mtime)
  fileinfo["mtime_obj"] = mtime_obj

  return fileinfo


def persist_file_info(filepath, fileinfo, dryrun=False, force=False):
  """Writes metadata into the file (except when dryrun is true).
  Existing metadata is not overwritten."""

  md = pyexiv2.ImageMetadata(filepath)
  md.read()
  if md.exif_keys or md.xmp_keys:
    if not force:
      print("Refusing to overwrite existing EXIF or XMP data in " + filepath, file=sys.stderr)
      return
    else:
      print("Forced to overwrite existing EXIF or XMP data in " + filepath, file=sys.stderr)

  datetime_obj = choose_best_datetime(fileinfo)
  to_write = {}
  datefieldnames = ['Exif.Image.DateTime', 'Exif.Photo.DateTimeDigitized',
    'Exif.Photo.DateTimeOriginal', 'Xmp.exif.DateTimeDigitized',
    'Xmp.exif.DateTimeOriginal', 'Xmp.xmp.CreateDate']
  for fieldname in datefieldnames:
    to_write[fieldname] = datetime_obj

  # XMP subject conveniently accepts python lists
  # maybe pass tags as command line parameters and d andfault to "Screenshot".
  #to_write["Xmp.dc.subject"] = ["Screenshot", "Testing"]
  to_write["Xmp.dc.subject"] = ["Screenshot"]

  for fieldname in to_write.keys():
    # delegating conversions to pyexiv2
    md[fieldname] = to_write[fieldname]
  if not dryrun:
    # write without changing mtime
    md.write(preserve_timestamps=True)
    print("Writing: " + str(to_write))
  else:
    print("Dryrun, not writing to file. Would write: " + str(to_write))



def main():
  args = sys.argv[1:]

  if not args:
    print('usage: [--dryrun] [--force] imagefile [imagefile ...] ')
    sys.exit(1)

  dryrun = False
  force = False
  # TODO: unforce order
  if args[0] == '--dryrun':
    dryrun = True
    del args[0]

  if args[0] == '--force':
    force = True
    del args[0]

  for filename in args:
    print("Processing: " + filename)
    filepath = os.path.abspath(filename)
    try:
      fileinfo = gather_file_info(filepath)
      #print(fileinfo)
      persist_file_info(filepath, fileinfo, dryrun, force)
    except InsufficientMetadataError as e:
      print("Error: " + e.message + " Skipping file.", file=sys.stderr)
    except UnsupportedFileTypeError as e:
      print("Error: " + e.message + " Skipping file.", file=sys.stderr)
    except (FileNotFoundError, OSError) as e:
      print("Error: " + str(e) + ". Skipping file.", file=sys.stderr)

    print()

if __name__ == '__main__':
  main()
