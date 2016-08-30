############
Intro
############

Cloud-fuse is an over-arching piece of software that is made work by plugins. The aim is to make it easy to create fully functional cloud file-systems from any cloud provider.

The plugins will only need to implement a few basic functions:

* list files
* upload file
* download file
* delete file

If possible, they should also implement:

* create folder
* delete folder
The system will gracefully handle object storage (such as amazon s3) which do not have proper folder support, whilst still making use of folders on other providers so as to keep the number of files in each directory to a minimum.

The plugins will declare at initialization whether they support directories.

We will store files in a block based form, with a configurable block size. This means that if you have large files and you would like to read only a small part of it (or if you wish to stream media) you will be able to download just the part you need rather than downloading the whole file. It also removes any limitations from the cloud provider on max filesize.
