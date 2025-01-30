import pytest
from src.agent.reflection.choose_best_option import EpicChooser, EpicSelection

class TestEpicChooser:
    @pytest.fixture
    def epic_chooser(self):
        """
        Fixture to create an EpicChooser instance for testing.
        """
        return EpicChooser(model='meta-llama/llama-3.2-3b-instruct')  # Specify model explicitly

    def test_format_epics(self, epic_chooser):
        """
        Test the epic formatting method.
        """
        epics = [
            "Build a simple todo list",
            "Develop a comprehensive project management system"
        ]
        formatted_epics = epic_chooser.format_epics(epics)
        
        assert "### Epic 1" in formatted_epics
        assert "### End of Epic 1" in formatted_epics
        assert "### Epic 2" in formatted_epics
        assert "### End of Epic 2" in formatted_epics
        assert len(formatted_epics.split("\n\n")) == 2

    def test_choose_best_epic(self, epic_chooser):
        """
        Test the epic selection method with a sample requirement and epics.
        """
        requirement = "Create a web application for task management"
        epics = [
            "Build a simple todo list with basic CRUD operations",
            "Develop a comprehensive project management system with user roles and advanced filtering",
            "Create a minimalist task tracker with real-time collaboration"
        ]
        
        result = epic_chooser.choose_best_epic(requirement, epics)
        
        assert isinstance(result, EpicSelection)
        assert result.chosen_epic_id is not None
        assert result.rationale is not None
        assert len(result.chosen_epic_id) > 0
        assert len(result.rationale) > 0

    def test_choose_best_epic_empty_list(self, epic_chooser):
        """
        Test epic selection with an empty list of epics.
        """
        requirement = "Create a web application"
        epics = []
        
        result = epic_chooser.choose_best_epic(requirement, epics)
        
        assert isinstance(result, EpicSelection)
        assert result.chosen_epic_id in ["error", "no_epics"]
        assert "Failed to select epic" in result.rationale or "No epics provided" in result.rationale

    @pytest.mark.parametrize("requirement,epics", [
        (
            "Develop a machine learning model for image classification",
            [
                "Use a simple CNN with fixed architecture",
                "Implement transfer learning with pre-trained models",
                "Create a custom deep learning architecture from scratch"
            ]
        ),
        (
            "Build a real-time chat application",
            [
                "Create a basic WebSocket-based chat",
                "Develop a scalable microservices-based chat platform",
                "Build a peer-to-peer encrypted messaging system"
            ]
        )
    ])
    def test_choose_best_epic_parametrized(self, epic_chooser, requirement, epics):
        """
        Parametrized test for epic selection with different scenarios.
        """
        result = epic_chooser.choose_best_epic(requirement, epics)
        
        assert isinstance(result, EpicSelection)
        assert result.chosen_epic_id is not None
        assert result.rationale is not None
        assert len(result.chosen_epic_id) > 0
        assert len(result.rationale) > 0
