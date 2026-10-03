from tools.graph.directory_type import directory_type


def test_known_directories_map_to_their_singular_type() -> None:
    assert directory_type("projects") == "project"
    assert directory_type("business") == "business"
    assert directory_type("people") == "person"
    assert directory_type("topics") == "topic"
    assert directory_type("personal") == "personal"


def test_an_unknown_directory_keeps_its_name() -> None:
    assert directory_type("notes") == "notes"
