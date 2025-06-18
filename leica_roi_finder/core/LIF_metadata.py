import struct
from lxml import etree
from typing import Tuple

def extract_lif_metadata(file_path: str) -> Tuple[str, int]:
    """
    Extracts XML metadata and a data offset from a LIF file

    Parameters
    ----------
    file_path : str
        Path to the LIF file.

    Returns
    -------
    xml_string : str
        XML metadata.
    data_offset : int
        The file offset
    """

    MAGIC_NUMBER_1 = 112
    MAGIC_NUMBER_2 = 42 # Block continuation marker

    # Extract XML element
    with open(file_path, 'rb') as f:
        header_val_1 = struct.unpack('<i', f.read(4))[0]
        if header_val_1 != MAGIC_NUMBER_1:
            raise ValueError(f'Invalid LIF file: {file_path}')

        f.read(4)

        header_val_2 = struct.unpack('<B', f.read(1))[0]
        if header_val_2 != MAGIC_NUMBER_2:
            raise ValueError(f'Invalid LIF file: {file_path}')

        xml_char_count = struct.unpack('<i', f.read(4))[0]

        xml_byte_length = xml_char_count * 2
        xml_bytes_utf16 = f.read(xml_byte_length)
        xml_description = xml_bytes_utf16.decode('utf-16')

        # Process memory blocks to find data offset
        data_offset = f.tell()

        while True:
            start_of_current_block_attempt = f.tell()

            block_prefix_bytes = f.read(17)
            if len(block_prefix_bytes) < 17:
                break 
            
            continuation_byte_data = f.read(1)
            if not continuation_byte_data:
                break
            
            continuation_byte = struct.unpack('<B', continuation_byte_data)[0]

            if continuation_byte != MAGIC_NUMBER_2:
                data_offset = start_of_current_block_attempt
                break

            block_id_len_bytes = f.read(4)
            if len(block_id_len_bytes) < 4:
                data_offset = start_of_current_block_attempt
                break
            
            block_id_char_count = struct.unpack('<i', block_id_len_bytes)[0]
            block_id_data_byte_length = block_id_char_count * 2
            block_id_data = f.read(block_id_data_byte_length)
            
            if len(block_id_data) < block_id_data_byte_length:
                data_offset = start_of_current_block_attempt
                break
            
            data_offset = f.tell()

    return xml_description, data_offset


def read_lif_metadata(file_path : str) -> dict:
    """
    Read metadata from a Leica LIF file

    Parameters
    ----------
    file_path : str
        File path of *.lif file

    Returns
    -------
    metadata : dict
        Dictionary containing relevant metadata for ROI finder

    Notes
    -----
    This function returns the following metadata that is required for the Leica ROI finder:
    - FlipX
    - FlipY
    - SwapXY
    - BitSize
    - MicroscopeModel
    - Offset
    - XDim
    - YDim
    - XRes
    - YRes
    - PosX
    - PosY

    This function has been tested and work for the Leica Stellaris 8
    Certain values might not have the same name in other microscope metadata
    """

    xml_description, position = extract_lif_metadata(file_path)
    root = etree.fromstring(xml_description)

    # Retrieve confocalsettings
    atl_element = root.find('.//ATLConfocalSettingDefinition')

    # Retrieve all relevant information
    atl_attributes = atl_element.attrib
    metadata = {
        "FlipX" : bool(int(atl_attributes["FlipX"])),
        "FlipY" : bool(int(atl_attributes["FlipY"])),
        "SwampXY" : bool(int(atl_attributes["SwapXY"])),
        "BitSize" : int(atl_attributes["BitSize"]),
        "MicroscopeModel" : str(atl_attributes["MicroscopeModel"]),
        "Offset" : position
    }

    # Retrieve dimensions
    atl_elements = root.findall('.//DimensionDescription')
    atl_attributes_list = [element.attrib for element in atl_elements]

    metadata['XDim'] = int(atl_attributes_list[0]['NumberOfElements'])
    metadata['YDim'] = int(atl_attributes_list[1]['NumberOfElements'])

    # Compute pixel size
    metadata['XRes'] = float(atl_attributes_list[0]['Length'])/(metadata['XDim']-1)
    metadata['YRes'] = float(atl_attributes_list[1]['Length'])/(metadata['YDim']-1)

    # Retrieve tilescan offset
    tile = root.find('.//Tile').attrib

    metadata["PosX"] = float(tile["PosX"])
    metadata["PosY"] = float(tile["PosY"])

    return metadata