import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import os

class XMindGenerator:
    def __init__(self):
        self.ns = {'xmind': 'urn:xmind:xmap:xmlns:content:2.0'}
        
    def create_topic(self, title, topic_id=None, subtopics=None):
        """Create a topic element with optional subtopics"""
        if topic_id is None:
            topic_id = f"topic_{len(title.replace(' ', '_'))}{datetime.now().microsecond}"
            
        topic = ET.Element('topic', id=topic_id)
        title_elem = ET.SubElement(topic, 'title')
        title_elem.text = title
        
        if subtopics:
            children = ET.SubElement(topic, 'children')
            topics_container = ET.SubElement(children, 'topics', type='attached')
            for subtopic in subtopics:
                topics_container.append(subtopic)
                
        return topic
    
    def create_mind_map(self, central_topic, main_branches):
        """Create the main mind map structure"""
        # Create root element
        root = ET.Element('xmap-content', 
                         xmlns='urn:xmind:xmap:xmlns:content:2.0', 
                         version='2.0')
        
        # Create sheet
        sheet = ET.SubElement(root, 'sheet', id='sheet1', theme='theme1')
        
        # Create central topic
        central = ET.SubElement(sheet, 'topic', id='root')
        central.set('structure-class', 'org.xmind.ui.map')
        central_title = ET.SubElement(central, 'title')
        central_title.text = central_topic
        
        # Add main branches
        if main_branches:
            children = ET.SubElement(central, 'children')
            topics_container = ET.SubElement(children, 'topics', type='attached')
            
            for branch in main_branches:
                topics_container.append(branch)
        
        return root
    
    def save_xmind_file(self, xml_content, filename):
        """Save XML content as XMind file (ZIP format)"""
        # Create required files
        files = {
            'content.xml': ET.tostring(xml_content, encoding='utf-8', xml_declaration=True),
            'META-INF/manifest.xml': b'''<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
    <file-entry full-path="content.xml" media-type="text/xml"/>
</manifest>''',
            'meta.xml': f'''<?xml version="1.0" encoding="UTF-8"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
    <Author>XMind Generator</Author>
    <Create-Time>{datetime.now().isoformat()}</Create-Time>
</meta>'''.encode('utf-8')
        }
        
        # Create ZIP file with .xmind extension
        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, content in files.items():
                zf.writestr(file_path, content)
        
        print(f"XMind file created: {filename}")

# Example usage
def create_sample_mind_map():
    generator = XMindGenerator()
    
    # Create subtopics
    subtopic1_1 = generator.create_topic("Research Phase")
    subtopic1_2 = generator.create_topic("Development Phase")
    subtopic1_3 = generator.create_topic("Testing Phase")
    
    subtopic2_1 = generator.create_topic("Team Meeting")
    subtopic2_2 = generator.create_topic("Client Review")
    
    # Create main branches
    branch1 = generator.create_topic("Project Timeline", 
                                   subtopics=[subtopic1_1, subtopic1_2, subtopic1_3])
    branch2 = generator.create_topic("Meetings", 
                                   subtopics=[subtopic2_1, subtopic2_2])
    branch3 = generator.create_topic("Resources")
    branch4 = generator.create_topic("Goals")
    
    # Create the complete mind map
    mind_map = generator.create_mind_map("My Project", 
                                       [branch1, branch2, branch3, branch4])
    
    # Save to file
    generator.save_xmind_file(mind_map, "generated_mindmap.xmind")

if __name__ == "__main__":
    create_sample_mind_map()