from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, FilePath, DirectoryPath, AnyUrl

from .errors import UnrootedResource

UriT = Union[FilePath, AnyUrl]
OptionsT = Optional[Union[Dict[str, str], List[Tuple[str, str]], List[str]]]
# todo: pending optional directories for output dirs that will be created,
# see: https://github.com/samuelcolvin/pydantic/issues/1254
# https://github.com/samuelcolvin/pydantic/issues/1983


class ResourceKind(Enum):
    Naive = 0  # we don't know how it's rooted
    Relative = 1  # it's a relative tree, base may lack context
    Absolute = 2  # it's a local absolute path
    FullyQualified = 3  # base is a full URI with scheme


class ManifestStoreKind(Enum):
    Naive = 0  # we don't know how it's stored
    Local = 1  # it's a local file we can immediately open
    Archive = 2  # represents part of an archive tar/zip/etc
    Network = 3  # it's a local absolute path


class Resource(BaseModel):
    """Describes some local or remote resource"""

    id: Optional[str]  # some abstract identifier
    uri: Union[FilePath, AnyUrl, Path]
    type: str = ""  # mimetype
    kind: ResourceKind = ResourceKind.Naive
    attrs: Dict[str, str] = {}
    meta: str = ""

    def is_localized(self):
        """Path is resolvable as a local resource, NOT necessarily existing locally"""
        if self.kind in (ResourceKind.Absolute, ResourceKind.Relative):
            # todo: I dunno if I wanna deal with relative squirrelyness here
            return True

        elif self.kind is ResourceKind.FullyQualified:
            if self.uri.startswith('file://'):
                return True

    def __fspath__(self):
        if self.is_localized():
            return str(self.uri)
        raise UnrootedResource(f"Cannot resolve absolute path: {self.uri}")


class Manifest(BaseModel):
    """A loose collection of elements"""

    base: Union[DirectoryPath, AnyUrl, Path]  # base of the manifest tree
    kind: ResourceKind = ResourceKind.Naive  # how is the manifest rooted?
    elements: List[Resource]  # manifest contents


class ManifestMap(BaseModel):
    """A Manifest which can be addressed by the relative paths"""

    base: Union[DirectoryPath, AnyUrl, Path]  # base of the manifest tree
    kind: ResourceKind = ResourceKind.Naive  # how is the manifest rooted?
    elements: Dict[Path, Resource]  # manifest contents


class SitoFileToFile(BaseModel):
    """File-in, file-out. Takes a single file (or URI), emits a single file (or URI) """

    input_uri: UriT
    output_uri: Optional[Union[FilePath, AnyUrl, str]]
    options: OptionsT


class SitoDirToDir(BaseModel):
    """Directory-in, directory-out. """

    input_dir: DirectoryPath
    output_dir: Optional[Union[DirectoryPath, str]]
    options: OptionsT


class SitoFileToDir(BaseModel):
    """Single file in, directory of files out. """

    input_uri: UriT
    output_dir: Optional[Union[DirectoryPath, str]]
    options: OptionsT


class SitoCoreUtil(BaseModel):
    """Emulates the interface of common coreutils tools, mv, tar, etc. E.g.:
    tool [options] [output] <input> [inputs...]"""

    inputs: List[UriT]
    output: Optional[UriT]
    options: OptionsT
