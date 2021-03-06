# Alteryx_SDK_Delete
Custom Alteryx tool to delete files from the filesystem. Files will be __permanently deleted without warning__.

## Installation
Download the yxi file and double click to install in Alteyrx. The tool will be installed in the __File System__ category.

![alt text](https://github.com/bobpeers/Alteryx_SDK_Delete/blob/master/images/Delete_toolbar.png "Alteryx File System Category")

## Requirements

This tool uses the standard Python libraries so no dependencies will be installed.

## Usage
This tool accepts a single input. The tool should be mapped to the __full path__ of the files to delete, usually provided by placing a Directory tool before this tool.

| __WARNING__ |
| --- |
| Files deleted using this tool will be __permanently__ deleted and are __not recoverable__. Use with care. You have been warned.|

## Outputs
Successful operations will be output to the O-Output. If the file could not be deleted (most likely due to __file locking__ issues) the output will be sent to the E-Output 
along with the error reason.

## Usage
This workflow demonstrates the tool in use and the output data.

![alt text](https://github.com/bobpeers/Alteryx_SDK_Delete/blob/master/images/Delete_workflow.png "Delete Workflow")
