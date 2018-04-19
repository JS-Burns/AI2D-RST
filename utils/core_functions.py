#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import json
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import os


class Annotate:
    """
    This class holds various functions for processing and parsing AI2D
    annotation.
    """
    def __init__(self):
        pass

    @staticmethod
    def load_annotation(path_to_annotation):
        """
        Loads AI2D annotation from a JSON file and returns the annotation as a
        dictionary.

        Parameters:
             path_to_annotation: A string containing the filepath to annotation.

        Returns:
             A dictionary containing AI2D annotation.
        """
        # Open the file containing the annotation
        with open(path_to_annotation) as annotation_file:
            # Parse the AI2D annotation from the JSON file into a dictionary
            annotation = json.load(annotation_file)

        # Return the annotation
        return annotation

    @staticmethod
    def group_nodes(graph, user_input):
        """
        A function for grouping together nodes of a graph, which are included in
        the accompanying list.
        
        Parameters:
            graph: A networkx graph.
            user_input: A list of nodes contained in the graph.

        Returns:
            An updated networkx graph.
        """
        # Create a dictionary of the kinds of nodes currently in the graph
        node_dict = Annotate.get_node_dict(graph)

        # Check the user input against the node dictionary
        input_node_types = [node_dict[u.upper()] for u in user_input]

        # If the user input contains an imageConsts, do not add an node
        if 'imageConsts' in input_node_types:
            for k, v in node_dict.items():
                if v == 'imageConsts':
                    for valid_elem in user_input:
                        graph.add_edge(valid_elem.upper(), k.upper())

        else:
            # Generate a name for the new node that joins together the elements
            # provided by the user
            new_node = '+'.join(user_input).upper()

            # Add the new node to the graph
            graph.add_node(new_node, kind='group')

            # Add edges from nodes in the user input to the new node
            for valid_elem in user_input:
                graph.add_edge(valid_elem.upper(), new_node)

        return graph

    @staticmethod
    def get_node_dict(graph, kind=None):
        """
        A function for creating a dictionary of nodes and their kind.
        
        Parameters:
            graph: A networkx graph.
            kind: A string defining what to include in the dictionary. 'node'
                  returns only nodes and 'group' returns only groups. By
                  default, the function returns all nodes defined in the graph.
    
        Returns:
            A dictionary with node names as keys and kind as values.
        """

        # Generate a dictionary with nodes and their kind
        node_types = nx.get_node_attributes(graph, 'kind')

        # If the requested output consists of node groups, return group dict
        if kind == 'group':

            # Generate a dictionary of groups
            group_dict = {k: k for k, v in node_types.items() if
                          v is 'group'}

            # Return dictionary
            return group_dict

        # If the requested output consists of nodes, return node dict
        if kind == 'node':

            # Generate a dictionary of nodes
            node_dict = {k: k for k, v in node_types.items() if v is not
                         'group'}

            # Return dictionary
            return node_dict

        # Otherwise return all node types
        else:
            return node_types

    @staticmethod
    def parse_annotation(annotation):
        """
        Parses AI2D annotation stored in a dictionary and prepares the
        annotation for drawing a graph.

        Parameters:
            annotation: A dictionary containing AI2D annotation.

        Returns:
            A dictionary for drawing a graph of the annotation.
        """
        # List types of diagram elements to be added to the graph
        targets = ['blobs', 'arrows', 'text', 'arrowHeads', 'containers',
                   'imageConsts']

        # Parse the diagram elements defined in the annotation, cast into list
        try:
            diagram_elements = [list(annotation[t].keys()) for t in targets]

            # Filter empty diagram types
            diagram_elements = list(filter(None, diagram_elements))

            # Flatten the resulting list
            diagram_elements = [i for sublist in diagram_elements
                                for i in sublist]

        except KeyError:
            pass

        # Parse the semantic relations defined in the annotation into a dict
        try:
            relations = annotation['relationships']

        except KeyError:
            pass

        return diagram_elements, relations

    @staticmethod
    def extract_element_type(elements, annotation):
        """
        Extracts the types of the identified diagram elements.

        Parameters:
            elements: A list of diagram elements.
            annotation: A dictionary of AI2D annotation.

        Returns:
             A dictionary with element types as keys and identifiers as values.
        """
        # Check for correct input type
        assert isinstance(elements, list)
        assert isinstance(annotation, dict)

        # Define the target categories for various diagram elements
        targets = ['arrowHeads', 'arrows', 'blobs', 'text', 'containers',
                   'imageConsts']

        # Create a dictionary for holding element types
        element_types = {}

        # Loop over the diagram elements
        for e in elements:

            try:
                # Search for matches in the target categories
                for t in targets:

                    # Get the identifiers for each element category
                    ids = [i for i in annotation[t].keys()]

                    # If the element is found among the identifiers, add the
                    # type to the dictionary
                    if e in ids:
                        element_types[e] = t

            # Skip if the category is not found
            except KeyError:
                continue

        # Return the element type dictionary
        return element_types

    @staticmethod
    def request_input(graph, layout):

        # Define available commands
        commands = ['info', 'comment', 'skip', 'exit', 'done']

        # Define a prompt for user input
        prompt = "Please enter members of element group or a valid command: "

        # Set a variable indicating that the annotation procedure is ongoing
        annotating = True

        # Enter a while loop for the annotation procedure
        while annotating:

            # Draw the graph
            diagram = Draw.draw_graph(graph)

            # Join the graph and the layout structure horizontally
            preview = np.hstack((diagram, layout))

            # Show the resulting visualization
            cv2.imshow("Annotation", preview)

            # Prompt user for input
            user_input = input(prompt)

            # Check if the input is a command
            if user_input in commands:

                # Quit the program immediately upon command
                if user_input == 'exit':
                    exit("Quitting ...")

                # If a skip is requested, return None and move to next example
                if user_input == 'skip':
                    return None

                # Print information if requested
                if user_input == 'info':

                    # Clear screen first
                    os.system('cls' if os.name == 'nt' else 'clear')

                    print("---\n"
                          "Enter the identifiers of elements you wish to group "
                          "together.\n"
                          "Separate the identifiers with a comma.\n"
                          "\n"
                          "Example of valid input: b1, a1, t1\n\n"
                          ""
                          "This command would group nodes B1, A1 and T1 under "
                          "a common node.\n"
                          "---\n"
                          "Valid commands include:\n"
                          "---\n"
                          "info: Print this message.\n"
                          "comment: Enter a comment about current diagram.\n"
                          "skip: Skip the current diagram.\n"
                          "exit: Exit the annotator immediately.\n"
                          "done: Mark current annotation completed.\n"
                          "---")
                    pass

                # Store a comment if requested
                if user_input == 'comment':

                    # Show a prompt for comment
                    comment = input("Enter comment: ")

                    # Return the comment
                    return comment

                # If the user marks the annotation as complete, freeze the graph
                if user_input == 'done':

                    # Freeze and return the graph
                    graph = nx.freeze(graph)

                    return graph

            # If user input does not include a valid command, assume the input
            # is a string containing a list of diagram elements.
            if user_input not in commands:

                # Split the input into a list
                user_input = user_input.split(', ')

                # Generate a list of valid diagram elements present in the graph
                valid_nodes = [e.lower() for e in graph.nodes]

                # Generate a dictionary of groups
                group_dict = Annotate.get_node_dict(graph, kind='group')

                # Count the current groups and enumerate for convenience. This
                # allows the user to refer to group number instead of complex
                # identifier.
                group_dict = {"g{}".format(i): k for i, (k, v) in
                              enumerate(group_dict.items(), start=1)}

                # Create a list of identifiers based on the dict keys
                valid_groups = [g.lower() for g in group_dict.keys()]

                # Combine the valid nodes and groups into a set
                valid_elems = set(valid_nodes + valid_groups)

                # Check for invalid input by comparing the user input and the
                # valid elements as sets.
                while not set(user_input).issubset(valid_elems):

                    # Get difference between user input and valid graph
                    diff = set(user_input).difference(valid_elems)

                    # Print error message with difference in sets.
                    print("Sorry, {} is not a valid diagram element or command."
                          " Please try again.".format(' '.join(diff)))

                    # Break from the loop
                    break

                # Proceed if the user input is a subset of valid elements
                if set(user_input).issubset(valid_elems):

                    # Replace aliases with valid identifiers, if used
                    user_input = [group_dict[u] if u in valid_groups else u for
                                  u in user_input]

                    # Update the graph according to user input
                    graph = Annotate.group_nodes(graph, user_input)

                # Continue until the annotation process is complete
                continue


class Draw:
    """
    This class holds various functions for visualizing AI2D annotation.
    """
    def __init__(self):
        pass

    @staticmethod
    def convert_colour(colour):
        """
        Converts a matplotlib colour name to BGR for OpenCV.

        Parameters:
            colour: A valid matplotlib colour name.

        Returns:
            A BGR three tuple.
        """
        # Convert matplotlib colour name to normalized RGB
        colour = matplotlib.colors.to_rgb(colour)

        # Multiply by 255 and round
        colour = tuple(round(255 * x) for x in colour)

        # Reverse the tuple for OpenCV
        return tuple(reversed(colour))

    @staticmethod
    def draw_graph_from_annotation(annotation, draw_edges=True,
                                   draw_arrowheads=True, return_graph=False):
        """
        Draws a graph of diagram elements parsed from AI2D annotation.

        Parameters:
            annotation: A dictionary parsed from AI2D JSON files.
            draw_edges: A boolean defining whether edges are to be drawn.
            draw_arrowheads: A boolean defining whether arrowheads are drawn.
            return_graph: A boolean defining whether a networkx graph is 
                          returned.

        Returns:
            An image visualising the graph; optionally, also the graph itself.
        """
        # Check for correct input type
        assert isinstance(annotation, dict)

        # Parse the annotation from the dictionary
        diagram_elements, relations = Annotate.parse_annotation(annotation)

        # Extract element types
        element_types = Annotate.extract_element_type(diagram_elements,
                                                      annotation)

        # Check if arrowheads should be excluded
        if not draw_arrowheads:

            # Remove arrowheads from the dictionary
            element_types = {k: v for k, v in element_types.items()
                             if v != 'arrowHeads'}

        # Set up a dictionary to track arrows and arrowheads
        arrowmap = {}

        # Create a new graph
        graph = nx.Graph()

        # Add diagram elements to the graph and record their type (kind)
        for element, kind in element_types.items():
            graph.add_node(element, kind=kind)

        # Draw edges between nodes if requested
        if draw_edges:

            # Loop over individual relations
            for relation, attributes in relations.items():

                # If the relation is 'arrowHeadTail', draw an edge between the
                # arrow and its head
                if attributes['category'] == 'arrowHeadTail':

                    graph.add_edge(attributes['origin'],
                                   attributes['destination'])

                    # Add arrowhead information to the dict for tracking arrows
                    arrowmap[attributes['origin']] = attributes['destination']

                # Next, check if the relation includes a connector
                try:
                    if attributes['connector']:

                        # Check if the connector (arrow) has an arrowhead
                        if attributes['connector'] in arrowmap.keys():

                            # First, draw an edge between origin and connector
                            graph.add_edge(attributes['origin'],
                                           attributes['connector'])

                            # Then draw an edge between arrowhead and
                            # destination, fetching the arrowhead identifier
                            # from the dictionary
                            graph.add_edge(arrowmap[attributes['connector']],
                                           attributes['destination'])

                        else:
                            # If the connector does not have an arrowhead, draw
                            # edge from origin to destination via the connector
                            graph.add_edge(attributes['origin'],
                                           attributes['connector'])

                            graph.add_edge(attributes['connector'],
                                           attributes['destination'])

                # If connector does not exist, draw a normal relation between
                # the origin and the destination
                except KeyError:
                    graph.add_edge(attributes['origin'],
                                   attributes['destination'])

        # Generate a label dictionary by taking the node attributes and removing
        # relations
        node_types = nx.get_node_attributes(graph, 'kind')
        label_dict = {k: k for k, v in node_types.items()}

        # Set up the matplotlib Figure and Axis
        fig = plt.figure(dpi=100)
        ax = fig.add_subplot(1, 1, 1)

        # Initialize a spring layout for the graph
        pos = nx.spring_layout(graph)

        # Draw nodes
        Draw.draw_nodes(graph, pos=pos, ax=ax, node_types=node_types,
                        draw_edges=True)

        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=10, labels=label_dict)

        # Remove margins from the graph and axes from the plot
        fig.tight_layout(pad=0)
        plt.axis('off')

        # Save figure to file, read the file using OpenCV and remove the file
        plt.savefig('temp.png')
        img = cv2.imread('temp.png')
        os.remove('temp.png')

        # Close the matplotlib plot
        plt.close()

        # Return requested objects
        if return_graph:
            return img, graph
        else:
            return img

    @staticmethod
    def draw_graph(graph, dpi=100):

        # Set up the matplotlib Figure, its resolution and Axis
        fig = plt.figure(dpi=dpi)
        ax = fig.add_subplot(1, 1, 1)

        # Initialize a spring layout for the graph
        pos = nx.spring_layout(graph)

        # Generate a dictionary with nodes and their kind
        node_types = nx.get_node_attributes(graph, 'kind')

        # Create label dictionaries for both nodes and groups of nodes
        node_dict = Annotate.get_node_dict(graph, kind='node')
        group_dict = Annotate.get_node_dict(graph, kind='group')

        # Enumerate groups and use their numbers as labels for clarity
        group_dict = {k: "G{}".format(i) for i, (k, v) in
                      enumerate(group_dict.items(), start=1)}

        # Draw nodes
        Draw.draw_nodes(graph, pos=pos, ax=ax, node_types=node_types)

        # Draw labels for nodes
        nx.draw_networkx_labels(graph, pos, font_size=10, labels=node_dict)

        # Draw labels for groups
        nx.draw_networkx_labels(graph, pos, font_size=10, labels=group_dict)

        # Remove margins from the graph and axes from the plot
        fig.tight_layout(pad=0)
        plt.axis('off')

        # Save figure to file, read the file using OpenCV and remove the file
        plt.savefig('temp.png')
        img = cv2.imread('temp.png')
        os.remove('temp.png')

        # Close matplotlib figure
        plt.close()

        return img

    @staticmethod
    def draw_nodes(graph, pos, ax, node_types, draw_edges=True):
        """
        A generic function for visualising the nodes in a graph.

        Parameters:
            graph: A networkx graph.
            pos: Positions for the networkx graph.
            ax: Matplotlib Figure Axis on which to draw.
            node_types: A dictionary of node types extracted from the graph.
            draw_edges: A boolean indicating whether edges should be drawn.
        
        Returns:
             None
        """
        # Attempt to draw nodes for text elements
        try:
            texts = [k for k, v in node_types.items() if v == 'text']
            nx.draw_networkx_nodes(graph, pos, nodelist=texts, alpha=1,
                                   node_color='dodgerblue', ax=ax)
        except KeyError:
            pass

        # Attempt to draw nodes for blobs
        try:
            blobs = [k for k, v in node_types.items() if v == 'blobs']
            nx.draw_networkx_nodes(graph, pos, nodelist=blobs, alpha=1,
                                   node_color='orangered', ax=ax)
        except KeyError:
            pass

        # Attempt to draw nodes for arrowheads
        try:
            arrowhs = [k for k, v in node_types.items() if v == 'arrowHeads']
            nx.draw_networkx_nodes(graph, pos, nodelist=arrowhs, alpha=1,
                                   node_color='darkorange', ax=ax)
        except KeyError:
            pass

        # Attempt to draw nodes for arrows
        try:
            arrows = [k for k, v in node_types.items() if v == 'arrows']
            nx.draw_networkx_nodes(graph, pos, nodelist=arrows, alpha=1,
                                   node_color='peachpuff', ax=ax)
        except KeyError:
            pass

        # Attempt to draw nodes for imageConsts
        try:
            constants = [k for k, v in node_types.items() if
                         v == 'imageConsts']
            nx.draw_networkx_nodes(graph, pos, nodelist=constants, alpha=1,
                                   node_color='palegoldenrod', ax=ax)
        except KeyError:
            pass

        # Attempt to draw nodes for element groups
        try:
            groups = [k for k, v in node_types.items() if v == 'group']
            nx.draw_networkx_nodes(graph, pos, nodelist=groups, alpha=1,
                                   node_color='navajowhite', ax=ax,
                                   node_size=50)
        except KeyError:
            pass

        # Draw edges if requested
        if draw_edges:
            # Draw edges between nodes
            nx.draw_networkx_edges(graph, pos, alpha=0.5, ax=ax)

# TODO Design a new approach based on class, which takes JSON as input
class Diagram:
    """
    This class holds the annotation for a single AI2D diagram.
    """
    def __init__(self, json_path, image_path, size=600):
        """
        This function initializes the Diagram class.
        
        Parameters:
            json_path: Path to the JSON file containing AI2D annotation.
            
        Returns:
            A Diagram with methods and attributes.
        """
        # Mark the annotation initially as not complete
        self.complete = False

        # Assign paths to JSON annotation and image to variables
        self.json_path = json_path
        self.image_path = image_path

        # Load JSON annotation into a dictionary
        self.annotation = self.load_annotation(json_path)

        # Parse the annotation dictionary for elements and relations
        self.elements, self.relations = self.parse_annotation(self.annotation)

        # Extract element types
        self.element_types = self.extract_types(self.elements, self.annotation)

        # Set visualisation size and visualise the layout annotation
        self.size = size
        self.layout = self.draw_layout(self.image_path, self.annotation,
                                       self.size)

    @staticmethod
    def load_annotation(json_path):
        """
        Loads AI2D annotation from a JSON file and returns the annotation as a
        dictionary.

        Parameters:
             json_path: A string containing the filepath to annotation.

        Returns:
             A dictionary containing AI2D annotation.
        """
        # Open the file containing the annotation
        with open(json_path) as annotation_file:

            # Parse the AI2D annotation from the JSON file into a dictionary
            annotation = json.load(annotation_file)

        # Return the annotation
        return annotation

    @staticmethod
    def parse_annotation(annotation):
        """
        Parses AI2D annotation stored in a dictionary and prepares the
        annotation for drawing a graph.

        Parameters:
            annotation: A dictionary containing AI2D annotation.

        Returns:
            A dictionary for drawing a graph of the annotation.
        """
        # List types of diagram elements to be added to the graph
        targets = ['blobs', 'arrows', 'text', 'arrowHeads', 'containers',
                   'imageConsts']

        # Parse the diagram elements defined in the annotation, cast into list
        try:
            diagram_elements = [list(annotation[t].keys()) for t in targets]

            # Filter empty diagram types
            diagram_elements = list(filter(None, diagram_elements))

            # Flatten the resulting list
            diagram_elements = [i for sublist in diagram_elements
                                for i in sublist]

        except KeyError:
            pass

        # Parse the semantic relations defined in the annotation into a dict
        try:
            relations = annotation['relationships']

        except KeyError:
            pass

        return diagram_elements, relations

    @staticmethod
    def extract_types(elements, annotation):
        """
        Extracts the types of the identified diagram elements.

        Parameters:
            elements: A list of diagram elements.
            annotation: A dictionary of AI2D annotation.

        Returns:
             A dictionary with element types as keys and identifiers as values.
        """
        # Check for correct input type
        assert isinstance(elements, list)
        assert isinstance(annotation, dict)

        # Define the target categories for various diagram elements
        targets = ['arrowHeads', 'arrows', 'blobs', 'text', 'containers',
                   'imageConsts']

        # Create a dictionary for holding element types
        element_types = {}

        # Loop over the diagram elements
        for e in elements:

            try:
                # Search for matches in the target categories
                for t in targets:

                    # Get the identifiers for each element category
                    ids = [i for i in annotation[t].keys()]

                    # If the element is found among the identifiers, add the
                    # type to the dictionary
                    if e in ids:
                        element_types[e] = t

            # Skip if the category is not found
            except KeyError:
                continue

        # Return the element type dictionary
        return element_types

    @staticmethod
    def draw_layout(path_to_image, annotation, size):

        # Load the diagram image and make a copy
        img = cv2.imread(path_to_image).copy()

        # Calculate aspect ratio (target width / current width) and new
        # width of the preview image.
        (h, w) = img.shape[:2]

        # Size according to the larger dimension (height / width)
        if h > w:
            r = size / h
            dim = (int(w * r), size)

        if w >= h:
            r = size / w
            dim = (size, int(h * r))

        # Resize the preview image
        img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

        # Begin by trying to draw the blobs.
        try:
            for b in annotation['blobs']:
                # Get blob ID
                blob_id = annotation['blobs'][b]['id']

                # Assign the blob points into a variable and convert into numpy
                # array
                points = np.array(annotation['blobs'][b]['polygon'], np.int32)

                # Scale the coordinates according to the ratio; convert to int
                points = np.round(points * r, decimals=0).astype('int')

                # Reshape the numpy array for drawing
                points = points.reshape((-1, 1, 2))

                # Compute center of the drawn element
                m = cv2.moments(points)
                x = int(m["m10"] / m["m00"])
                y = int(m["m01"] / m["m00"])

                # Draw the polygon. Note that points must be in brackets to
                # be drawn as lines; otherwise only points will appear.
                cv2.polylines(img, [points], isClosed=True, thickness=2,
                              lineType=cv2.LINE_AA,
                              color=Draw.convert_colour('orangered'))

                # Insert the identifier into the middle of the element
                cv2.putText(img, blob_id, (x - 10, y + 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=1, lineType=cv2.LINE_AA, thickness=1,
                            color=Draw.convert_colour('magenta'))

        # Skip if there are no blobs to draw
        except KeyError:
            pass

        # Next, attempt to draw text blocks
        try:
            for t in annotation['text']:
                # Get text id
                text_id = annotation['text'][t]['id']

                # Get the start and end points of the rectangle and cast
                # them into tuples for drawing.
                rect = annotation['text'][t]['rectangle']

                # Scale the coordinates according to the ratio; convert to int
                rect[0] = [np.round(x * r, decimals=0).astype('int')
                           for x in rect[0]]
                rect[1] = [np.round(x * r, decimals=0).astype('int')
                           for x in rect[1]]

                # Get start and end coordinates for the rectangle
                start, end = tuple(rect[0]), tuple(rect[1])

                # Get center of rectangle; cast into integer
                c = (round((start[0] + end[0]) / 2 - 10).astype('int'),
                     round((start[1] + end[1]) / 2 + 10).astype('int'))

                # Draw the rectangle
                cv2.rectangle(img, start, end, thickness=2,
                              lineType=cv2.LINE_AA,
                              color=Draw.convert_colour('dodgerblue'))

                # Insert the identifier into the middle of the element
                cv2.putText(img, text_id, c, cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=1, lineType=cv2.LINE_AA, thickness=1,
                            color=Draw.convert_colour('magenta'))

        # Skip if there are no text boxes to draw
        except KeyError:
            pass

        # Finally, attempt to draw any arrows
        try:
            for a in annotation['arrows']:
                # Get arrow id
                arrow_id = annotation['arrows'][a]['id']

                # Assign the points into a variable
                points = np.array(annotation['arrows'][a]['polygon'], np.int32)

                # Scale the coordinates according to the ratio; convert to int
                points = np.round(points * r, decimals=0).astype('int')

                # Reshape the numpy array for drawing
                points = points.reshape((-1, 1, 2))

                # Compute center of the drawn element
                m = cv2.moments(points)
                x = int(m["m10"] / m["m00"])
                y = int(m["m01"] / m["m00"])

                # Draw the polygon. Note that points must be in brackets to
                # be drawn as lines; otherwise only points will appear.
                cv2.polylines(img, [points], isClosed=True, thickness=2,
                              lineType=cv2.LINE_AA,
                              color=Draw.convert_colour('peachpuff'))

                # Insert the identifier into the middle of the element
                cv2.putText(img, arrow_id, (x - 10, y + 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=1, color=Draw.convert_colour('magenta'),
                            lineType=cv2.LINE_AA, thickness=1)

        # Skip if there are no arrows to draw
        except KeyError:
            pass

        # Show the resulting visualization
        cv2.imshow("Image", img)
        cv2.waitKey()

        return img

