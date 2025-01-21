from bs4 import BeautifulSoup, NavigableString, Tag
import json

class HTMLParser:
    def __init__(self, html_content=None):
        self.soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
        self.tree = None
        self.title = None
        self.combined_text = ""
        self.image_links = []
        self.social_links = {
            'youtube': set(),
            'twitter': set(),
            'instagram': set(),
            'linkedin': set(),
            'facebook': set()
        }
        self.nav_links = set()
        self.general_links = set()

    def clean_html(self):
        if self.soup:
            body = self.soup.body
            if body:
                for style in body.find_all('style'):
                    style.decompose()
                for script in body.find_all('script'):
                    script.decompose()
                for tag in body.find_all(True):
                    if 'style' in tag.attrs:
                        del tag.attrs['style']
                    tag.attrs = {k: v for k, v in tag.attrs.items() if not k.startswith('on')}

    def extract_title(self):
        if self.soup:
            title_tag = self.soup.title
            self.title = title_tag.string if title_tag else None

    def extract_text_and_links(self):
        if self.soup:
            body = self.soup.body
            if body:
                text_set = set()
                image_links = set()
                text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']
                for tag in body.find_all(text_tags):
                    text = tag.get_text(strip=True)
                    if text:
                        text_set.add(text)
                    for img in tag.find_all('img'):
                        if 'src' in img.attrs:
                            image_links.add(img['src'])
                self.combined_text = ' '.join(text_set)
                self.image_links = list(image_links)

    def extract_social_and_nav_links(self):
        if self.soup:
            body = self.soup.body
            if body:
                for a_tag in body.find_all('a'):
                    href = a_tag.get('href', '')
                    if href and not href.startswith('#'):
                        self.nav_links.add(href)
                        href_lower = href.lower()
                        if 'youtube.com' in href_lower or 'youtu.be' in href_lower:
                            self.social_links['youtube'].add(href)
                        elif 'twitter.com' in href_lower:
                            self.social_links['twitter'].add(href)
                        elif 'instagram.com' in href_lower:
                            self.social_links['instagram'].add(href)
                        elif 'linkedin.com' in href_lower:
                            self.social_links['linkedin'].add(href)
                        elif 'facebook.com' in href_lower or 'fb.com' in href_lower:
                            self.social_links['facebook'].add(href)
                        else:
                            self.general_links.add(href)

    def store_semantics(self):
        def process_element(element):
            if not hasattr(element, 'name') or element.name is None:
                return None
            semantic_node = {
                "tag": element.name,
                "attributes": element.attrs,
                "content": []
            }
            has_children = False
            for content_item in element.contents:
                if isinstance(content_item, NavigableString):
                    text = content_item.strip()
                    if text:
                        semantic_node["content"].append(text)
                elif isinstance(content_item, Tag):
                    child_node = process_element(content_item)
                    if child_node:
                        semantic_node["content"].append(child_node)
                has_children = True
            if not has_children:
                semantic_node["text"] = str(element.get_text(strip=True))
            if not semantic_node["content"] and "text" not in semantic_node:
                return None
            return semantic_node
        if self.soup:
            body = self.soup.body
            if body:
                root_node = process_element(body)
                if root_node:
                    self.tree = root_node

    def convert_to_markdown(self):
        markdown_content = ""
        if self.title:
            markdown_content += f"# {self.title}\n\n"
        if self.tree:
            markdown_content += self.tree_to_markdown(self.tree)
        return markdown_content

    def tree_to_markdown(self, node, parent_tag=None, indent=0):
        content = ""
        if isinstance(node, dict):
            tag = node.get("tag")
            if tag is None:
                return ""
            if "text" in node:
                if tag in ["h1", "h2", "h3"]:
                    level = int(tag[1])
                    content += f"{'#' * level} {node['text']}\n\n"
                elif tag == "img":
                    if "attributes" in node and "src" in node["attributes"]:
                        content += f"![]({node['attributes']['src']})\n\n"
                elif tag == "a":
                    if "attributes" in node and "href" in node["attributes"]:
                        href = node["attributes"]["href"]
                        if not href.startswith('#'):
                            content += f"[{node['text']}]({href}) "
                elif tag in ["strong", "em"]:
                    start_tag = "**" if tag == "strong" else "*"
                    end_tag = "**" if tag == "strong" else "*"
                    content += f"{start_tag}{node['text']}{end_tag}"
                else:
                    content += node['text']
            else:
                if tag == "p":
                    for item in node.get("content", []):
                        if isinstance(item, str):
                            content += item
                        else:
                            content += self.tree_to_markdown(item, parent_tag="p", indent=indent)
                    content += "\n\n"
                elif tag == "ul":
                    for item in node.get("content", []):
                        if isinstance(item, dict) and item.get("tag") == "li":
                            content += f"{' ' * indent}* {self.tree_to_markdown(item, parent_tag='ul', indent=indent + 2)}"
                    content += "\n"
                elif tag == "ol":
                    count = 1
                    for item in node.get("content", []):
                        if isinstance(item, dict) and item.get("tag") == "li":
                            content += f"{' ' * indent}{count}. {self.tree_to_markdown(item, parent_tag='ol', indent=indent + 2)}"
                            count += 1
                    content += "\n"
                elif tag == "li":
                    for item in node.get("content", []):
                        if isinstance(item, str):
                            content += item
                        else:
                            content += self.tree_to_markdown(item, parent_tag="li", indent=indent)
                    content += "\n"
                else:
                    for item in node.get("content", []):
                        if isinstance(item, str):
                            content += item
                        else:
                            content += self.tree_to_markdown(item, parent_tag=tag, indent=indent)
        elif isinstance(node, str):
            content += node
        return content

    def parse(self, output_file=None):
        if not self.soup:
            return {}
        self.extract_title()
        self.clean_html()
        self.extract_text_and_links()
        self.extract_social_and_nav_links()
        self.store_semantics()
        if not self.combined_text.strip():
            self.combined_text = None
        if not self.image_links:
            self.image_links = None
        if not self.general_links:
            self.general_links = None
        if not self.nav_links:
            self.nav_links = None
        if not any(self.social_links.values()):
            self.social_links = None
        if output_file:
            self.save_tree(output_file)
        return {
            'title': self.title,
            'tree': self.tree,
            'text': self.combined_text,
            'images': self.image_links,
            'navigation': list(self.nav_links),
            'social_media': {k: list(v) for k, v in self.social_links.items()},
            'links': list(self.general_links)
        }

    def save_tree(self, output_file):
        with open(output_file, 'w') as f:
            json.dump(self.tree, f, indent=4)