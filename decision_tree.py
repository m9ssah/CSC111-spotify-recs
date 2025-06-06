"""CSC111 Project 2: Spotify Recommendation System - Decision Tree

This module contains functions for fitting a decision tree to a music dataset,
enabling song recommendations based on a randomly selected song.

We have marked each place you to modify code with the word "TODO" in order to run the file.
"""

# Standard Library imports
from __future__ import annotations
import random
from collections import Counter
from typing import Any, Optional
import python_ta

# Third-Party Library imports
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import graphviz
from graphviz import Source


class Node:
    """A class representing a node in the decision tree.

    Instance Attributes:
        - feature: The index of the feature (column) used to split the data at this node.
        - threshold: The threshold value for the feature used to split the data.
        - left: The left child node.
        - right: The right child node.
        - value: The class label or predicted value of the node. This is used only in leaf nodes.
        It is the majority class or predicted label at this node.
    """
    feature: Optional[int]
    threshold: Optional[float]
    left: Optional[Node]
    right: Optional[Node]
    value: Optional[Any]

    def __init__(self, feature: Optional[int] = None, threshold: Optional[float] = None,
                 left: Optional[Node] = None, right: Optional[Node] = None,
                 value: Optional[int] = None) -> None:
        """Initialize a Node class."""
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    def is_leaf_node(self) -> None:
        """Returns whether the node is a leaf node."""
        return self.value is not None


class DecisionTree:
    """A class representing a decision tree that manages the song recommendation system.

    Instance Attributes:
        - min_samples_split: The minimum number of samples required to split an internal node.
        - max_depth: The maximum depth of the decision tree. Limits the tree's growth to prevent overfitting.
        - n_features: The number of features to consider when looking for the best split.
        If None, all features are considered.
        - root: The root node of the decision tree.
    """
    min_samples_split: int
    max_depth: int
    n_features: Optional[int]
    root: Optional[Node]

    def __init__(self, min_samples_split: int = 2, max_depth: int = 5, n_features: Optional[int] = None) -> None:
        """Initializes a DecisionTree class."""
        self.min_samples_split = min_samples_split
        self.max_depth = max_depth
        self.n_features = n_features
        self.root = None

    def fit(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Fits a decision tree to the dataset."""
        # check that self.n_features is not more than the actual number of features
        self.n_features = x_data.shape[1] if not self.n_features else min(x_data.shape[1], self.n_features)
        self.root = self._grow_tree(x_data, y_data)  # builds a decision tree based on the training data

    def _grow_tree(self, x_data: np.ndarray, y_data: np.ndarray, depth: int = 0) -> Node:
        """Recursively grows the decision tree."""
        n_samples, n_feats = x_data.shape  # get the number of samples and the number of features in the current node
        n_labels = len(np.unique(y_data))  # get the number of unique labels in the target variable

        # check the stopping criteria
        if depth >= self.max_depth or n_labels == 1 or n_samples < self.min_samples_split:
            # stop growing and return the most common label at this node
            leaf_value = self._most_common_label(y_data)
            return Node(value=leaf_value)

        # only select unique features
        feat_idxs = np.random.choice(n_feats, self.n_features, replace=False)

        # find the best split
        best_feature, best_threshold = self._best_split(x_data, y_data, feat_idxs)

        # create child nodes
        left_idxs, right_idxs = self._split(x_data[:, best_feature], best_threshold)
        left = self._grow_tree(x_data[left_idxs, :], y_data[left_idxs], depth + 1)
        right = self._grow_tree(x_data[right_idxs, :], y_data[right_idxs], depth + 1)

        return Node(feature=best_feature, threshold=best_threshold, left=left, right=right)

    def _best_split(self, x_data: np.ndarray, y_data: np.ndarray,
                    feat_idxs: list[int]) -> tuple[Optional[int], Optional[float]]:
        """Find the best threshold among all possible thresholds."""
        best_gain = -1
        split_idx, split_threshold = None, None

        for feat_idx in feat_idxs:
            x_column = x_data[:, feat_idx]
            thresholds = np.unique(x_column)

            for threshold in thresholds:
                # calculate the information gain
                gain = self._information_gain(y_data, x_column, threshold)

                if gain > best_gain:
                    best_gain = gain
                    split_idx = feat_idx
                    split_threshold = threshold

        return split_idx, split_threshold

    def _information_gain(self, y_data: np.ndarray, x_column: np.ndarray, threshold: float) -> float:
        """Compute the information gain from splitting a dataset at a given threshold.

        Preconditions:
            - y.size > 0
            - X.column.size == y.size
        """
        # parent entropy
        parent_entropy = self._entropy(y_data)

        # create children
        left_idxs, right_idxs = self._split(x_column, threshold)

        if len(left_idxs) == 0 or len(right_idxs) == 0:  # check if either are empty
            return 0

        # calculate weighted entropy of children
        n = len(y_data)
        n_left, n_right = len(left_idxs), len(right_idxs)
        entropy_left, entropy_right = self._entropy(y_data[left_idxs]), self._entropy(y_data[right_idxs])
        child_entropy = (n_left / n) * entropy_left + (n_right / n) * entropy_right

        # calculate information gain
        information_gain = parent_entropy - child_entropy
        return information_gain

    def _split(self, x_column: np.ndarray, split_threshold: float) -> tuple[np.ndarray, np.ndarray]:
        """Split the dataset into two groups based on the given split_threshold.

        Preconditions:
            - X.column.size > 0
        """
        left_idxs = np.argwhere(x_column <= split_threshold).flatten()
        right_idxs = np.argwhere(x_column > split_threshold).flatten()
        return left_idxs, right_idxs

    def _entropy(self, y_data: np.ndarray) -> float:
        """Calculate the entropy of a given set of labels.

        The entropy is a measure of the impurity or uncertainty in the labels.
        It ranges from 0 (no uncertainty) to log2(n) (maximum uncertainty).
        """
        hist = np.bincount(y_data)
        prob = hist / len(y_data)
        return -np.sum(prob * np.log2(prob + 1e-9))

    def _most_common_label(self, y_data: np.ndarray) -> Optional[int]:
        """Find the most common label in the dataset."""
        if len(y_data) == 0:
            return None
        counter = Counter(y_data)
        return counter.most_common(1)[0][0]

    def predict(self, x_data: np.ndarray) -> np.ndarray:
        """Predict class labels for a given dataset using the trained decision tree.

        Preconditions:
            - self.root is not None
        """
        return np.array([self._traverse_tree(x, self.root) for x in x_data])

    def _traverse_tree(self, x: np.ndarray, node: Node) -> int:
        """Recursively traverse the decision tree to classify a single sample.

        If the current node is a leaf, return its stored class label. Otherwise, continue
        traversing based on the feature's threshold.

        Preconditions:
            - node is not None
            - x.size > 0 (the input sample must have at least one feature)
        """
        if node.is_leaf_node():  # base case
            return node.value
        else:
            if x[node.feature] <= node.threshold:
                return self._traverse_tree(x, node.left)
            else:
                return self._traverse_tree(x, node.right)


def recommend_songs(dtree: DecisionTree, user_song: str, features: list[str],
                    dataset: pd.DataFrame) -> Optional[list[tuple[str, str, float]]]:
    """Recommend a similar song to the given user_song using the decision tree dtree and cosine similarity.

    Preconditions:
        - dtree is a trained DecisionTree object
        - user_song is a valid song name in the dataset
        - features is a list of feature names that exist in the dataset
        - dataset is a pandas DataFrame containing at least the column names: 'name', 'artists'
        and the specified features.
    """

    # find user_song features in the dataset
    user_song_features = get_song_features(user_song, features, dataset)

    # get the leaf nodes of the decision
    user_song_features_df = pd.DataFrame([user_song_features])
    leaf_node_prediction = dtree.predict(user_song_features_df.to_numpy())[0]

    # using LabelEncoder to map the leaf node back to the song name
    encoder = LabelEncoder()
    encoder.fit(dataset['name'])  # fit the encoder on the dataset's song names
    predicted_song_name = encoder.inverse_transform([leaf_node_prediction])[0]

    # extract songs that belong to the predicted leaf node
    leaf_node_songs = dataset[dataset['name'] == predicted_song_name]

    # remove duplicates
    leaf_node_songs = leaf_node_songs.drop_duplicates(subset='name')

    if len(leaf_node_songs) == 0:
        print("No songs found in this leaf node.")
        return None

    # begin finding similar songs
    similarities = []
    user_song_vector = np.array(list(user_song_features.values())).reshape(1, -1)

    for _, row in leaf_node_songs.iterrows():
        song_features = row.to_dict()
        song_features_values = {k: v for k, v in song_features.items() if k in user_song_features}
        song_vector = np.array(list(song_features_values.values())).reshape(1, -1)

        similarity = calculate_cosine_similarity(user_song_vector, song_vector)  # using helper function below
        song_name = row['name'].strip()  # ensure no extra whitespace
        artist_name = row['artists']
        similarities.append((song_name, artist_name, similarity))  # append song name, artist, and similarity

    # rank and filter by similarity
    similarities = [item for item in similarities if item[2] != -1]  # filter out invalid similarities
    similarities.sort(key=lambda x: x[2], reverse=True)

    # remove duplicates
    seen = set()
    rec_songs = []
    for song_name, artists_names, similarity in similarities:
        if song_name not in seen:
            rec_songs.append((song_name, artists_names, similarity))
            seen.add(song_name)

    return rec_songs


def calculate_cosine_similarity(user_song_vector: np.ndarray, song_vector: np.ndarray) -> float:
    """Calculates the cosine similarity between the feature vectors of the user's song and a song from the dataset.
    If the shapes of the feature vectors for the user song and dataset song do not match, it returns -1.
    """
    if user_song_vector.shape == song_vector.shape:  # check if user song and dataset song have the same dimensions
        return cosine_similarity(user_song_vector, song_vector)
    else:
        return -1  # default value for missing similarity


def get_song_features(user_song: str, features: list[str], dataset: pd.DataFrame) -> dict[str, float]:
    """Returns the feature values for a specific song from the dataset.

    Representation Invariants:
        - `dataset` must contain a 'name' column and all features specified in `features`.
        - All elements in `features` must be valid column names in `dataset`.
    """

    # filter the dataset to get the row corresponding to user_song
    song_row = dataset[dataset['name'] == user_song]

    if song_row.empty:
        raise ValueError(f"Song '{user_song}' not found in the dataset.")

    # extract the requested features for the song and convert to a dictionary
    user_song_features = song_row[features].iloc[0].to_dict()

    return user_song_features


def visualize_custom_tree(node: Node, feature_names: list[str], classnames: list[str], dot_data: Optional[str] = None,
                          parent: Optional[str] = None, depth: Optional[int] = 0) -> Optional[Source]:
    """Recursively traverse the tree and create Graphviz dot representation."""
    if dot_data is None:
        dot_data = "digraph Tree {\n"  # indicates start of the tree representation

    if node.is_leaf_node():  # if it is a leaf node, label with class name
        class_name = classnames[node.value]
        class_name = class_name.replace('"', '\\"')  # get rid of quotes in class name
        dot_data += f'    node{depth} [label="{class_name}"];\n'
        if parent is not None:  # if the node is not the root, add edge between parent node to current leaf node
            dot_data += f'    node{parent} -> node{depth};\n'
    else:  # if it is an internal node, label with feature names and thresholds
        feature_name = feature_names[node.feature]
        feature_name = feature_name.replace('"', '\\"')  # get rid of quotes in class name
        dot_data += f'    node{depth} [label="{feature_name} <= {node.threshold:.2f}"];\n'
        if parent is not None:
            dot_data += f'    node{parent} -> node{depth};\n'

        dot_data = visualize_custom_tree(node.left, feature_names, classnames, dot_data, parent=depth, depth=depth + 1)
        dot_data = visualize_custom_tree(node.right, feature_names, classnames,
                                         dot_data, parent=depth, depth=depth + 1)

    if depth == 0:  # once all the nodes and edges are processed
        dot_data += "}\n"
        return Source(dot_data)

    return dot_data  # return dot data when the function is not at root level (i.e. depth > 0)


def plot_tree(dtree: DecisionTree, feature_names: list[str], classnames: list[str], filename: str = 'tree') -> None:
    """Generate the tree visualization and save to a file."""
    graph = visualize_custom_tree(dtree.root, feature_names, classnames)
    print(graph.source)
    graph.render(filename, format='png')
    print(f"Tree visualization saved to {filename}.png")


if __name__ == "__main__":
    # python_ta.check_all(config={
    #     'extra-imports': [
    #         'os', 'random', 'collections', 'typing', 'numpy', 'pandas',
    #         'sklearn.model_selection', 'sklearn.metrics', 'sklearn.metrics.pairwise',
    #         'sklearn.preprocessing', 'graphviz', 'python_ta'
    #     ],
    #     'allowed-io': ['plot_tree', 'recommend_songs'],
    #     'max-line-length': 120
    # })

    # define constants for the features used in the model and the dataset limit
    FEATURES = ['speechiness', 'tempo', 'energy', 'loudness', 'acousticness', 'danceability', 'instrumentalness']
    LIMIT = 5000  # limit the dataset size to LIMIT rows to reduce running time during testing

    # DATA WRANGLING
    # TODO: replace path-to-file
    df = pd.read_csv('/Users/jemimasilaen/.cache/kagglehub/datasets/bwandowando/spotify'
                     '-songs-with-attributes-and-lyrics/versions/19/songs_with_attributes_and_lyrics.csv')
    df = df.dropna(subset=FEATURES)
    df = df.head(LIMIT)

    # generating a random index for demo purposes
    random_index = random.randint(0, LIMIT)

    # retrieve the song name at the random index
    SONG = df.iloc[random_index]['name']
    ARTISTS = df.iloc[random_index]['artists']
    print(f"Searching for similar songs for '{SONG}' by {ARTISTS}")

    print(f"Searching through {df.shape[0]} songs...")

    # convert pandas DataFrame (X) and pandas Series (y) to numpy arrays
    X = df[FEATURES].to_numpy()
    y = df['name'].to_numpy()  # the target value is song

    # encode the 'song' column as categories
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    class_names = le.classes_.tolist()

    assert np.min(y_encoded) >= 0, "y should contain non-negative values"

    # split the data into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=4321)

    # initialize the decision tree
    clf = DecisionTree(min_samples_split=2, max_depth=7)
    clf.fit(X_train, y_train)

    # (Optional) visualize tree
    plot_tree(dtree=clf, feature_names=FEATURES, classnames=class_names, filename="song_recommendation_tree")

    # get song recommendations
    recommended_songs = recommend_songs(dtree=clf, user_song=SONG, features=FEATURES, dataset=df)

    print("Recommended songs:")
    for song, artists, _ in recommended_songs:
        print(f"Song: {song}, Artist: {artists}")

    # (Optional) evaluate the accuracy of the model on the test set
    # the accuracy is based on the dataset's constraints
    accuracy = accuracy_score(y_test, clf.predict(X_test))
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
