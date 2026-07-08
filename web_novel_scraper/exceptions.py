"""Central exception definitions for the web-novel-scraper project."""


## BASE EXCEPTIONS


class ScraperError(Exception):
    """Default Exception for Scraper Exceptions"""


## NOVEL ERRORS


class NovelNotFoundError(ScraperError):
    """Default Exception for Scraper Exceptions"""


## NETWORK & REQUEST EXCEPTIONS


class RequestError(ScraperError):
    """Exception raised for any exception for request operations"""


class FlaresolverrError(RequestError):
    pass


class FlaresolverrConnectionError(FlaresolverrError):
    pass


class CommonGetRequestError(RequestError):
    pass


class FlaresolverrRequestError(RequestError):
    pass


class InvalidURLError(RequestError):
    pass


class ResponseError(RequestError):
    pass


class InvalidFlaresolverrResponseError(ResponseError):
    pass


class ResponseIsEmptyError(ResponseError):
    pass


## FILE & I/O OPERATIONS EXCEPTIONS


class IOUtilsError(ScraperError):
    """Exception raised for any exception for file operations"""


class InvalidPathError(IOUtilsError):
    """Exception raised for invalid path"""


class EmptyDirError(IOUtilsError):
    pass


class EmptyFileError(IOUtilsError):
    pass


class FileNotFoundCustomError(IOUtilsError):
    """Exception raised when file is not found"""


class InvalidFileTypeError(IOUtilsError):
    """Exception raised for invalid file type"""


class OSCustomError(IOUtilsError):
    """Exception raised for OS-related errors"""


class JsonParseError(IOUtilsError):
    """Exception raised when JSON parsing fails"""


class InvalidJsonTypeError(IOUtilsError):
    """Exception raised for invalid JSON type"""


## NOVEL DATA EXCEPTIONS


class NovelDataError(ScraperError):
    pass


## LOAD NOVEL DATA EXCEPTIONS


class LoadNovelDataError(NovelDataError):
    pass


class InvalidNovelDataDirError(LoadNovelDataError):
    pass


class InvalidNovelDataError(LoadNovelDataError):
    pass


class NovelDataNotFoundError(LoadNovelDataError):
    pass


class SaveNovelDataError(NovelDataError):
    pass


class DeleteNovelDataError(NovelDataError):
    pass


#


class ChapterFileNotFoundError(NovelDataError):
    pass


class ChapterFileIsEmptyError(NovelDataError):
    pass


class UpdateTOCMetadataError(NovelDataError):
    pass


class TOCFragmentNotFoundError(NovelDataError):
    pass


class TOCFragmentFileIsEmptyError(NovelDataError):
    pass


class CoverImageNotFoundError(NovelDataError):
    pass


class CoverImageFileIsEmptyError(NovelDataError):
    pass


## VALIDATION & DATA EXCEPTIONS


class ValidationError(ScraperError):
    """Exception raised for any exception for invalid values"""


## CONFIG EXCEPTIONS


class ConfigError(ScraperError):
    pass


class ConfigNotInitializedError(ConfigError):
    pass


class InvalidTypeConfigError(ConfigError):
    pass


class LoadConfigError(ConfigError):
    pass


class LoadHostConfigError(ConfigError):
    pass


class HostNotInHostConfigFileError(LoadHostConfigError):
    pass


class EmptyConfigFileError(LoadConfigError):
    pass


class ConfigFileNotFoundError(LoadConfigError):
    pass


class ParseConfigOptionError(ConfigError):
    pass


class ConfigKeyConflictError(ParseConfigOptionError):
    pass


class ParametersParseError(ConfigError):
    pass


class InvalidParameterStructureError(ParametersParseError):
    """Exception raised when parameter structure is invalid"""


class ParameterKeyConflictError(ParametersParseError):
    """Exception raised when parameter keys conflict"""


class ParameterKeyFormatError(ParametersParseError):
    """Exception raised when parameter key format is invalid"""


class ParameterValueFormatError(ParametersParseError):
    """Exception raised when parameter key format is invalid"""


## DECODE EXCEPTIONS


class DecodeError(ScraperError):
    """Exception raised for any exception for decoding operations"""


class HTMLParseError(DecodeError):
    """Raised when HTML parsing fails"""


class ContentExtractionError(DecodeError):
    """Raised when content extraction fails"""


class DecodeProcessorError(DecodeError):
    """Raised when there is an error in a decoder processor"""


class HostNotExistsError(DecodeError):
    """Raised when the host doesn't exist on the Decode Guide"""


## DECODE GUIDE EXCEPTIONS


class DecodeGuideError(DecodeError):
    pass


class LoadDecodeGuideError(DecodeGuideError):
    """Exception raised when loading decode guide fails"""


class InvalidDecodeGuideError(LoadDecodeGuideError):
    pass


class DecodeGuideNotFoundError(LoadDecodeGuideError):
    pass


class DecodeGuideIsEmptyError(LoadDecodeGuideError):
    pass


class HostNotInDecodeGuideError(LoadDecodeGuideError):
    """Exception raised when host is not found in decode guide"""


## NOVEL & DIRECTORY EXCEPTIONS


class NovelBaseDirError(ScraperError):
    pass


class InvalidNovelBaseDirError(NovelBaseDirError):
    """Exception raised for invalid novel base directory"""


class InvalidMetaFileError(NovelBaseDirError):
    """Exception raised for invalid metadata file"""


## EXPORT EXCEPTIONS


class ExportError(ScraperError):
    pass


class ExportFormatNotSupportedError(ExportError):
    pass


class InvalidChapterRangeError(ExportError):
    pass


class InvalidStartChapterFromChapterRangeError(InvalidChapterRangeError):
    pass


class InvalidEndChapterFromChapterRangeError(InvalidChapterRangeError):
    pass


class InvalidChapterByBookFromChapterRangeError(InvalidChapterRangeError):
    pass


class InvalidOutputDirectoryError(ExportError):
    pass


class ExporterError(ExportError):
    pass


class SaveBookError(ExporterError):
    pass


class ExportChapterError(ExporterError):
    pass


class ChapterContentNotFoundError(ExportChapterError):
    pass


class ChapterTitleNotFoundError(ExportChapterError):
    pass
