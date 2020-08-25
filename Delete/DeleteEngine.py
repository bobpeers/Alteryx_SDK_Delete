import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import os

class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.SourceFieldName: str = None
        
        self.input: IncomingInterface = None
        self.output: Sdk.OutputAnchor = None
        self.error_output : sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.SourceFieldName = Et.fromstring(str_xml).find('SourceField').text if 'SourceField' in str_xml else None

        # Validity checks.
        if self.SourceFieldName is None:
            self.display_error_msg('Source field cannot be empty.')

        # Getting the output anchor from Config.xml by the output connection name
        self.output = self.output_anchor_mgr.get_output_anchor('Output')
        self.error_output = self.output_anchor_mgr.get_output_anchor("ErrorOutput")

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        #self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return True

    def pi_close(self, b_has_errors: bool):
        self.output.assert_close()
        self.error_output.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)

    def display_info(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.record_copier: Sdk.RecordCopier = None
        self.record_creator: Sdk.RecordCreator = None
        self.OutputField: Sdk.Field = None
        self.SourceField: Sdk.Field = None
        self.DestField: Sdk.Field = None

        #output field config
        self.output_name: str = 'Delete Result'
        self.output_type: Sdk.FieldType = Sdk.FieldType.string
        self.output_size: int = 1000

        self.record_count = 0

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Make sure the user provided a field to parse
        if self.parent.SourceFieldName is None:
            self.parent.display_error_msg('Select a source field')
            return False
            
        # Get information about the source path field
        self.SourceField = record_info_in.get_field_by_name(self.parent.SourceFieldName)

        # Returns a new, empty RecordCreator object that is identical to record_info_in.
        record_info_out = record_info_in.clone()

        # Adds field to record with specified name and output type.
        self.OutputField = record_info_out.add_field(self.output_name, self.output_type, self.output_size)

        # Lets the downstream tools know what the outgoing record metadata will look like
        self.parent.output.init(record_info_out)
        self.parent.error_output.init(record_info_out)

        # Creating a new, empty record creator based on record_info_out's record layout.
        self.record_creator = record_info_out.construct_record_creator()

        # Instantiate a new instance of the RecordCopier class.
        self.record_copier = Sdk.RecordCopier(record_info_out, record_info_in)

        # Map each column of the input to where we want in the output.
        for index in range(record_info_in.num_fields):
            # Adding a field index mapping.
            self.record_copier.add(index, index)

        # Let record copier know that all field mappings have been added.
        self.record_copier.done_adding()

        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        # Copy the data from the incoming record into the outgoing record.
        self.record_creator.reset()
        self.record_copier.copy(self.record_creator, in_record)

        # Get the text to parse and set the matches counter
        source: str = self.SourceField.get_as_string(in_record)

        output_str: str = ''
        failed_op: bool = False

        # Check if value is null
        if source is not None:
            try:
                if not os.path.exists(source):
                    output_str = 'Source file doesn\'t exist'
                    failed_op = True
                elif os.path.isfile(source) or os.path.islink(source):
                    os.remove(source)
                    output_str = 'File deleted'
                else:
                    failed_op = True
                    output_str = 'Nothing to delete'
            except (IOError, os.error) as e:
                    failed_op = True
                    output_str = str(e)

            self.OutputField.set_from_string(self.record_creator, output_str)
            out_record = self.record_creator.finalize_record()
            if failed_op:
                self.parent.error_output.push_record(out_record)
            else:
                self.parent.output.push_record(out_record)
            self.record_count += 1

        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.output.update_progress(d_percent)

    def ii_close(self):
        # Close outgoing connections.
        self.parent.display_info(f'Processed {self.record_count} records')

        self.parent.output.close()
        self.parent.error_output.close()
