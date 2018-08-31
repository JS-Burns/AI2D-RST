# -*- coding: utf-8 -*-

from .draw import *
from .interface import *
from .parse import *

import cv2
import numpy as np
import os


class Diagram:
    """
    This class holds the annotation for a single AI2D-RST diagram.
    """
    def __init__(self, json, image):
        """
        This function initializes the Diagram class.
        
        Parameters:
            json: Path to the JSON file containing the original AI2D annotation 
                  or a dictionary containing parsed annotation.
            image: Path to the image file containing the diagram.
            
        Returns:
            An AI2D Diagram object with various methods and attributes.
        """
        # Mark the annotation initially as not complete
        self.complete = False

        # TODO Create separate completion flags for layout / rst

        # Set image path
        self.image_path = image

        # Continue by checking the annotation type. If the input is a dictionary
        # assign the dictionary to the variable 'annotation'.
        if type(json) == dict:
            self.annotation = json

        else:
            # Load JSON annotation into a dictionary
            self.annotation = load_annotation(json)

        # Create initial graph with diagram elements only
        self.graph = create_graph(self.annotation,
                                  edges=False,
                                  arrowheads=False)

        # Visualise the layout annotation in an image
        self.layout = draw_layout(self.image_path, self.annotation, 480)

        # Set up placeholders for the layout graph and comments
        self.comments = []

    def create_relation(self, rst_graph, user_input):
        """
        A function for drawing an RST relation between several diagram elements.
        
        Parameters:
            rst_graph: A NetworkX Graph.
            user_input: A string containing the name of a valid RST relation.
             
        Returns:
             An updated NetworkX Graph.
        """
        # Retrieve the name and kind of the RST relation
        relation_name = rst_relations[user_input]['name']
        relation_kind = rst_relations[user_input]['kind']

        # Create a dictionary of the nodes currently in the graph
        node_ix = get_node_dict(rst_graph, kind='node')

        # Generate a list of valid diagram elements present in the graph
        valid_nodes = [e.lower() for e in node_ix.keys()]

        # Generate a dictionary of RST relations present in the graph
        relation_ix = get_node_dict(rst_graph, kind='relation')

        # Loop through current RST relations and rename them for convenience.
        # This allows the user to refer to the relation identifier (e.g. r1)
        # instead of a complex relation ID (e.g. B0-T1+B9) during annotation.
        relation_ix = {"r{}".format(i): k for i, (k, v) in
                       enumerate(relation_ix.items(), start=1)}

        print("[DEBUG] Relation dictionary: {}".format(relation_ix))

        # Create a list of valid relation identifiers based on the dict keys
        valid_rels = [r.lower() for r in relation_ix.keys()]

        # Combine the valid nodes and relations into a single set
        valid_ids = set(valid_nodes + valid_rels)

        # Check whether the RST relation is mono- or multinuclear. Start with
        # mononuclear relations.
        if relation_kind == 'mono':

            # Request the identifier of the nucleus in the RST relation
            nucleus = input(prompts['nucleus_id'])

            # Split the user input into a list and convert to lowercase
            nucleus = nucleus.split()
            nucleus = [n.lower() for n in nucleus]

            # Check the total number of inputs in the list
            if len(nucleus) != 1:

                # Print error message and return
                print(messages['nucleus_err'])

                return

            # Check the user input against the set of valid identifiers
            if not set(nucleus).issubset(valid_ids):

                # If the user input is not a subset of valid identifiers, print
                # error message and return
                print("Sorry, {} is not a valid identifier. Please try "
                      "again.".format(nucleus))

                return

            else:

                # The input is valid, continue to process satellites
                pass

            # Request the identifier(s) of the satellite(s) in the RST relation
            satellites = input(prompts['satellite_id'])

            # Split the user input into a list and convert to lowercase
            satellites = satellites.split()
            satellites = [s.lower() for s in satellites]

            # Check the user input against the set of valid identifiers
            if not set(satellites).issubset(valid_ids):

                # Get difference between user input and valid graph
                diff = set(satellites).difference(valid_ids)

                # If the user input is not a subset of valid identifiers, print
                # error message and return
                print("Sorry, {} is not a valid diagram element or command."
                      " Please try again.".format(' '.join(diff)))

                return

            else:

                # If the input is valid, generate a name for the new relation
                new_relation = ''.join(nucleus).upper() + '-' + \
                               '+'.join(satellites).upper()

                # Add a new node to the graph to represent the RST relation
                rst_graph.add_node(new_relation,
                                   kind='relation',
                                   nucleus=nucleus,
                                   satellites=satellites,
                                   name=relation_name,
                                   id=new_relation
                                   )

                # Draw edges from satellite(s) to the current RST relation
                for s in satellites:

                    # Check if the satellites include another RST relation
                    if s in relation_ix.keys():

                        # Fetch the origin node from the dictionary of relations
                        satellite_rel = relation_ix[s]

                        # Add edge from satellite relation to the new relation
                        rst_graph.add_edge(satellite_rel, new_relation)

                    # If the satellite is not a relation, draw edge from node
                    else:

                        # Add edge to graph
                        rst_graph.add_edge(s.upper(), new_relation)

                # Draw edges from nucleus to relation
                for n in nucleus:

                    # Add edge to graph
                    rst_graph.add_edge(n.upper(), new_relation)

        # Continue by checking if the relation is multinuclear
        if relation_kind == 'multi':

            # Request the identifiers of the nuclei in the RST relation
            nuclei = input(prompts['nuclei_id'])

            # Split the user input into a list and convert to lowercase
            nuclei = nuclei.split()
            nuclei = [n.lower() for n in nuclei]

            # Check the total number of inputs in the list
            if len(nuclei) <= 1:

                # Print error message and return
                print(messages['nuclei_err'])

                return

            # Check the user input against the set of valid identifiers
            if not set(nuclei).issubset(valid_ids):

                # Get the difference between user input and valid ID sets
                diff = set(nuclei).difference(valid_ids)

                # Print error message with difference in sets
                print("Sorry, {} is not a valid diagram element or command. "
                      "Please try again.".format(' '.join(diff)))

                return

            # If the input is valid, continue to draw the relations
            else:

                # Generate a name for the new relation
                new_relation = '+'.join(nuclei).upper()

                # Add a new node to the graph to represent the RST relation
                rst_graph.add_node(new_relation,
                                   kind='relation',
                                   nuclei=nuclei,
                                   name=relation_name,
                                   id=new_relation)

                # Draw edges from nuclei to the current RST relation
                for n in nuclei:

                    # Check if the nuclei include another RST relation
                    if n in relation_ix.keys():

                        # Fetch the origin node from the relation index
                        origin = relation_ix[n]

                        # Add edge from the RST relation acting as nuclei to the
                        # current RST relation
                        rst_graph.add_edge(origin, new_relation)

                    # If all nuclei are nodes, draw edges to the RST relation
                    else:

                        # Add edge to graph
                        rst_graph.add_edge(n.upper(), new_relation)

    def group_nodes(self, graph, user_input):
        """
        A function for grouping together nodes of a graph, which are included in
        the accompanying list.

        Parameters:
            graph: A NetworkX Graph.
            user_input: A list of nodes contained in the graph.

        Returns:
            An updated NetworkX Graph.
        """
        # Create a dictionary of the nodes currently in the graph
        node_dict = get_node_dict(graph)

        # Check the user input against the node dictionary
        input_node_types = [node_dict[u.upper()] for u in user_input]

        # If the user input contains an imageConsts, do not add a node
        if 'imageConsts' in input_node_types:
            for k, v in node_dict.items():
                if v == 'imageConsts':
                    for valid_elem in user_input:
                        self.graph.add_edge(valid_elem.upper(), k.upper())

        else:
            # Generate a name for the new node that joins together the elements
            # provided by the user
            new_node = '+'.join(user_input).upper()

            # Add the new node to the graph
            self.graph.add_node(new_node, kind='group')

            # Add edges from nodes in the user input to the new node
            for valid_elem in user_input:
                self.graph.add_edge(valid_elem.upper(), new_node)

    def annotate_layout(self):
        """
        A function for annotating the logical / layout structure (DPG-L) of a
        diagram.
        
        Parameters:
            None. The function modifies the graph that is created when a Diagram
            object is initialised.
        
        Returns:
            Updates the graph contained in the Diagram object (self.graph)
            according to the user input.
        """

        # Enter a while loop for the annotation procedure
        while not self.complete:

            # Draw the graph
            diagram = draw_graph(self.graph, dpi=100)

            # Join the graph and the layout structure horizontally
            preview = np.hstack((diagram, self.layout))

            # Show the resulting visualization
            cv2.imshow("Annotation", preview)

            # Prompt user for input
            user_input = input(prompts['layout_default'])

            # Check if the input is a command
            if user_input in commands['layout']:

                # Quit the program immediately upon command
                if user_input == 'exit':

                    exit("Quitting ...")

                # If next diagram is requested, store current graph and move on
                if user_input == 'next':

                    # Destroy any remaining windows
                    cv2.destroyAllWindows()

                    return

                # Print information if requested
                if user_input == 'info':

                    # Clear screen first
                    os.system('cls' if os.name == 'nt' else 'clear')

                    # Print information on layout commands
                    print(info['layout'])

                    pass

                # Store a comment if requested
                if user_input == 'comment':

                    # Show a prompt for comment
                    comment = input(prompts['comment'])

                    # Return the comment
                    self.comments.append(comment)

                # If the user marks the annotation as complete
                if user_input == 'done':

                    # Set status to complete
                    self.complete = True

                    # Destroy any remaining windows
                    cv2.destroyAllWindows()

                    return

                # Save a screenshot if requested
                if user_input == 'cap':

                    # Get filename of current image
                    fname = os.path.basename(self.image_path)

                    # Write image on disk
                    cv2.imwrite("screen_capture_{}.png".format(fname), preview)

            # Check if the user has requested to delete a grouping node
            if 'rm' in user_input:

                # Get list of groups to delete
                user_input = user_input.lower().split()[1:]

                # Generate a dictionary of groups
                group_dict = get_node_dict(self.graph, kind='group')

                # Count the current groups and enumerate for convenience. This
                # allows the user to refer to group number instead of complex
                # identifier.
                group_dict = {"g{}".format(i): k for i, (k, v) in
                              enumerate(group_dict.items(), start=1)}

                # Check for invalid input by comparing the user input and the
                # valid group identifiers as sets.
                while not set(user_input).issubset(set(group_dict.keys())):

                    # Get difference between user input and valid graph
                    diff = set(user_input).difference(set(group_dict.keys()))

                    # Print error message with difference in sets.
                    print("Sorry, {} is not a valid group identifier."
                          " Please try again.".format(' '.join(diff)))

                    # Break from the loop
                    break

                # Proceed if the user input is a subset of valid group ids
                if set(user_input).issubset(group_dict.keys()):

                    # Replace aliases with valid identifiers, if used
                    user_input = [group_dict[u] if u in group_dict.keys()
                                  else u for u in user_input]

                    # Update the graph according to user input
                    self.graph.remove_nodes_from(user_input)

                    continue

            # If user input does not include a valid command, assume the input
            # is a string containing a list of diagram elements.
            elif user_input not in commands['layout']:

                # Split the input into a list
                user_input = user_input.split(',')

                # Strip extra whitespace
                user_input = [u.strip() for u in user_input]

                # Generate a list of valid diagram elements present in the graph
                valid_nodes = [e.lower() for e in self.graph.nodes]

                # Generate a dictionary of groups
                group_dict = get_node_dict(self.graph, kind='group')

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

                    # Get difference between user input and valid element sets
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
                    self.group_nodes(self.graph, user_input)

                # Continue until the annotation process is complete
                continue

    def annotate_rst(self):
        """
        A function for annotating the rhetorical structure (DPG-R) of a diagram.
        
        Parameters:
            None.
        
        Returns:
            Updates the RST graph in the Diagram object (self.rst_graph).
        """

        # TODO Check if an RST graph is complete: use a non-method flag for now
        rst_complete = False

        # Create a graph for RST annotation
        rst_graph = create_graph(self.annotation,
                                 edges=False,
                                 arrowheads=False,
                                 mode='rst'
                                 )

        # Enter a while loop for the annotation procedure
        while not rst_complete:

            # Draw the graph using RST mode
            diagram = draw_graph(rst_graph, dpi=100, mode='rst')

            # Join the graph and the layout structure horizontally
            preview = np.hstack((diagram, self.layout))

            # Show the resulting visualization
            cv2.imshow("Annotation", preview)

            # Prompt user for input
            user_input = input(prompts['rst_default'])

            # Check the input
            if user_input in commands['rst']:

                # Quit the program immediately upon command
                if user_input == 'exit':
                    exit("Quitting ...")

                # If next diagram is requested, store current graph and move on
                if user_input == 'next':

                    # Destroy any remaining windows
                    cv2.destroyAllWindows()

                    return

                # If the user marks the annotation as complete, change status
                if user_input == 'done':

                    # Set status to complete
                    rst_complete = True

                    # Destroy any remaining windows
                    cv2.destroyAllWindows()

                    return

                # If the user requests a list of available RST relations, print
                # the keys and their definitions.
                if user_input == 'relations':

                    # Clear screen first
                    os.system('cls' if os.name == 'nt' else 'clear')

                    # Loop over RST relations
                    for k, v in rst_relations.items():

                        # Print information on each RST relation
                        print("{} - abbreviation: {}, type: {}.".format(
                            v['name'].upper(),
                            k,
                            v['kind']))

                    pass

                # Print information if requested
                if user_input == 'info':

                    # Clear screen first
                    os.system('cls' if os.name == 'nt' else 'clear')

                    # Print information on layout commands
                    print(info['rst'])

                    pass

                # Store a comment if requested
                if user_input == 'comment':

                    # Show a prompt for comment
                    comment = input(prompts['comment'])

                    # Return the comment
                    self.comments.append(comment)

                # Save a screenshot if requested
                if user_input == 'cap':

                    # Get filename of current image
                    fname = os.path.basename(self.image_path)

                    # Write image on disk
                    cv2.imwrite("screen_capture_{}.png".format(fname), preview)

                # TODO Rest of the commands go here

                # If the user input is a new relation, request additional input
                if user_input == 'new':

                    # Request relation name
                    relation = input(prompts['rel_prompt'])

                    # Strip extra whitespace and convert the input to lowercase
                    relation = relation.strip().lower()

                    # Check that the input is a valid relation
                    if relation in rst_relations.keys():

                        # Create a rhetorical relation and add to graph
                        self.create_relation(rst_graph, relation)

                    else:
                        print("Sorry, {} is not a valid relation."
                              .format(relation))

            if user_input not in commands['rst']:

                # Print error message
                print("Sorry, {} is not a valid command.".format(user_input))

                continue

        pass