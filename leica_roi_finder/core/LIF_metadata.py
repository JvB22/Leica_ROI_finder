import struct
from lxml import etree

def read_lif_metadata(file_path):
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
    - SwampXY
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

    with open(file_path, 'rb') as f:
        # Basic LIF validation
        testvalue = struct.unpack('i', f.read(4))[0]
        if testvalue != 112:
            raise ValueError(f'Error Opening LIF-File: {file_path}')
        _ = struct.unpack('i', f.read(4))[0]
        testvalue = struct.unpack('B', f.read(1))[0]
        if testvalue != 42:
            raise ValueError(f'Error Opening LIF-File: {file_path}')
        testvalue = struct.unpack('i', f.read(4))[0]
        
        # Retrieve XML
        XMLObjDescriptionUTF16 = f.read(testvalue * 2)
        XMLObjDescription = XMLObjDescriptionUTF16.decode('utf-16')

        # Retrieve offset for memory map
        while True:
            data = f.read(4)
            testvalue = struct.unpack('i', data)[0]
            _ = struct.unpack('i', f.read(4))[0]
            testvalue = struct.unpack('B', f.read(1))[0]
            MemorySize = struct.unpack('q', f.read(8))[0]
            testvalue = struct.unpack('B', f.read(1))[0]
            if testvalue != 42:
                break
            testvalue = struct.unpack('i', f.read(4))[0]
            BlockIDLength = testvalue
            BlockIDData = f.read(BlockIDLength * 2)
            position = f.tell()

    root = etree.fromstring(XMLObjDescription)

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