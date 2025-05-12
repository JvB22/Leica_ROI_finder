import xml.etree.ElementTree as ET
import uuid
from xml.dom import minidom

def generate_coords_xml(coordinates, group_name=None):
    """
    Generates XML simulating a Leica .rgn file

    Parameters
    ----------
    coordinates : np.ndarray
        Numpy array containing coordinates, must be of shape (len, 2)
    group_name : str | None, default=None
        Group name to save the regions under

    Returns
    -------
    pretty_xml : str
        XML string containing coordinates
    """

    # Create root element
    root = ET.Element("StageOverviewRegions")
    
    # Create Regions element
    regions = ET.SubElement(root, "Regions")
    shape_list = ET.SubElement(regions, "ShapeList")
    items = ET.SubElement(shape_list, "Items")
    
    # Store identifiers to use later in StackList
    identifiers = []
    
    # Check if points should be grouped
    if group_name:
        # Create a compound shape to hold the points
        compound_item = ET.SubElement(items, "Item0")
        
        # Set group attributes
        ET.SubElement(compound_item, "Name").text = group_name
        compound_id = str(uuid.uuid4())
        ET.SubElement(compound_item, "Identifier").text = compound_id
        ET.SubElement(compound_item, "Type").text = "CompoundShape"
        ET.SubElement(compound_item, "Fill").text = "R:1 ,G: 0,B: 0,A: 0"
        ET.SubElement(compound_item, "Font")
        
        # Create empty verticies
        verticies = ET.SubElement(compound_item, "Verticies")
        ET.SubElement(verticies, "Items")
        
        # Create empty decorator colors
        decorator_colors = ET.SubElement(compound_item, "DecoratorColors")
        ET.SubElement(decorator_colors, "Items")
        
        # Create empty extended properties
        extended_props = ET.SubElement(compound_item, "ExtendedProperties")
        ET.SubElement(extended_props, "Items")
        
        # Create children container
        children = ET.SubElement(compound_item, "Children")
        children_items = ET.SubElement(children, "Items")
        
        # Points will be added to the children_items
        points_container = children_items
    else:
        # Points will be added directly to the main items
        points_container = items
    
    # Add point items
    for i, (x, y) in enumerate(coordinates):
        # Create item element with proper name (Item0, Item1, etc.)
        item = ET.SubElement(points_container, f"Item{i}")
        
        # Generate a unique identifier (UUID)
        identifier = str(uuid.uuid4())
        identifiers.append(identifier)
        
        # Create subelements for the item
        ET.SubElement(item, "Number").text = str((i + 1) * 2 + 7)  # Just an example increment
        
        # Add Name element if using CompoundShape
        if group_name:
            ET.SubElement(item, "Name").text = f"P{i+1}"
            
        ET.SubElement(item, "Tag").text = f"P {i + 1}"
        ET.SubElement(item, "Identifier").text = identifier
        ET.SubElement(item, "Type").text = "Point"
        ET.SubElement(item, "Fill").text = "R:1 ,G: 0,B: 0,A: 0"
        ET.SubElement(item, "Font")
        
        # Create verticies element
        verticies = ET.SubElement(item, "Verticies")
        verticies_items = ET.SubElement(verticies, "Items")
        vertex_item = ET.SubElement(verticies_items, "Item0")
        
        # Add X and Y coordinates
        ET.SubElement(vertex_item, "X").text = f"{x:.11f}"
        ET.SubElement(vertex_item, "Y").text = f"{y:.11f}"
        
        # Add empty elements
        decorator_colors = ET.SubElement(item, "DecoratorColors")
        ET.SubElement(decorator_colors, "Items")
        extended_props = ET.SubElement(item, "ExtendedProperties")
        ET.SubElement(extended_props, "Items")
    
    # Add attributes to ShapeList
    ET.SubElement(shape_list, "FillMaskMode").text = "None"
    ET.SubElement(shape_list, "VertexUnitMode").text = "Pixels"
    
    # Create StackList
    stack_list = ET.SubElement(root, "StackList")
    
    # Add entries to StackList
    for identifier in identifiers:
        entry = ET.SubElement(stack_list, "Entry")
        entry.set("Identifier", identifier)
        entry.set("Begin", "0.0000000000")
        entry.set("End", "0.0000000000")
        entry.set("SectionCount", "0")
        entry.set("ReferenceX", "0.0000000000")
        entry.set("ReferenceY", "0.0000000000")
        entry.set("FocusStabilizerOffset", "0.0000000000")
        entry.set("FocusStabilizerOffsetFixed", "false")
        entry.set("StackValid", "false")
        entry.set("Marked", "false")
    
    # Convert the ElementTree to a string with pretty formatting
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    return pretty_xml