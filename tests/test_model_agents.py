import pytest
from PIL import Image
from overeasy import *
from overeasy.models import *
from overeasy.types import Detections
from pydantic import BaseModel
import os

ROOT = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT, "outputs")

bounding_box_models = [
    GroundingDINO(type=GroundingDINOModel.Pretrain_1_8M),
    GroundingDINO(type=GroundingDINOModel.SwinB),
    GroundingDINO(type=GroundingDINOModel.SwinT),
    YOLOWorld(model="yolov8s-worldv2"),
    YOLOWorld(model="yolov8m-worldv2"),
    YOLOWorld(model="yolov8l-worldv2"),
    YOLOWorld(model="yolov8s-world"),
    YOLOWorld(model="yolov8m-world"),
    YOLOWorld(model="yolov8l-world"),
    OwlV2(),
    DETIC()
]
multimodal_llms = [
    GPTVision(model="gpt-4o"), 
    Gemini(model="gemini-1.5-flash"), 
    Claude(model="claude-3-5-sonnet-20240620"), 
    QwenVL(model_type="base"), 
    QwenVL(model_type="int4")
]
llms = [GPT(model="gpt-3.5-turbo"), GPT(model="gpt-4-turbo")]
captioning_models = [*multimodal_llms] 
classification_models = [LaionCLIP(), CLIP(), BiomedCLIP()]
ocr_models = [*multimodal_llms] 


@pytest.fixture
def count_eggs_image():
    image_path = os.path.join(ROOT, "count_eggs.jpg")
    return Image.open(image_path)

@pytest.fixture
def license_plate_image():
    image_path = os.path.join(ROOT, "plate.jpg")
    return Image.open(image_path)

@pytest.fixture(params=bounding_box_models)
def bounding_box_select_workflow(request) -> Workflow:
    model = request.param
    workflow = Workflow([
        BoundingBoxSelectAgent(classes=["egg"], model=model),
    ])
    return workflow

@pytest.fixture(params=multimodal_llms)
def vision_prompt_workflow(request) -> Workflow:  
    model = request.param
    workflow = Workflow([
        VisionPromptAgent(query="How many eggs are in this image?", model=model)
    ])
    return workflow

@pytest.fixture(params=captioning_models)
def dense_captioning_workflow(request) -> Workflow:
    model = request.param
    workflow = Workflow([
        DenseCaptioningAgent(model=model)
    ])
    return workflow

@pytest.fixture(params=llms)
def text_prompt_workflow(request) -> Workflow:
    model = request.param
    workflow = Workflow([
        DenseCaptioningAgent(model=GPTVision()),
        TextPromptAgent(query="How many eggs did you count in the description?", model=model)
    ])
    return workflow

@pytest.fixture
def binary_choice_workflow() -> Workflow:
    workflow = Workflow([
        BinaryChoiceAgent(query="Are there more than 5 eggs in this image?", model=GPTVision())
    ])
    return workflow

@pytest.fixture(params=classification_models)
def classification_workflow(request) -> Workflow:
    model = request.param
    workflow = Workflow([
        ClassificationAgent(classes=["0-5 eggs", "6-10 eggs", "11+ eggs"], model=model)
    ])
    return workflow

@pytest.fixture(params=ocr_models)
def ocr_workflow(request) -> Workflow:
    model = request.param
    workflow = Workflow([
        OCRAgent(model=model)
    ])
    return workflow

class EggCount(BaseModel):
    count: int

@pytest.fixture
def instructor_image_workflow() -> Workflow:
    workflow = Workflow([
        InstructorImageAgent(response_model=EggCount)
    ])
    return workflow

@pytest.fixture
def instructor_text_workflow() -> Workflow:
    workflow = Workflow([
        DenseCaptioningAgent(model=GPTVision()),
        InstructorTextAgent(response_model=EggCount)
    ])
    return workflow


def test_bounding_box_select_agent(bounding_box_select_workflow: Workflow, count_eggs_image):
    result, graph = bounding_box_select_workflow.execute(count_eggs_image)
    detections = result[0].data
    assert isinstance(detections, Detections)

    name = (bounding_box_select_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"bounding_box_select_{name}.png"))

def test_vision_prompt_agent(vision_prompt_workflow: Workflow, count_eggs_image):
    result, graph = vision_prompt_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, str)
    name = (vision_prompt_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"vision_prompt_{name}.png"))
    
def test_dense_captioning_agent(dense_captioning_workflow: Workflow, count_eggs_image):
    result, graph = dense_captioning_workflow.execute(count_eggs_image)
    assert isinstance(result[0].data, str)
    name = (dense_captioning_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"dense_captioning_{name}.png"))

def test_text_prompt_agent(text_prompt_workflow: Workflow, count_eggs_image):
    result, graph = text_prompt_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, str) 
    name = (text_prompt_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"text_prompt_{name}.png"))


def test_binary_choice_agent(binary_choice_workflow: Workflow, count_eggs_image):
    result, graph = binary_choice_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, Detections)
    # assert response.class_names[0] == "yes", "Incorrect binary choice"
    name = (binary_choice_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"binary_choice_{name}.png"))

def test_classification_agent(classification_workflow: Workflow, count_eggs_image):
    result, graph = classification_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, Detections)

    name = (classification_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"classification_{name}.png"))

def test_ocr_agent(ocr_workflow: Workflow, license_plate_image):
    result, graph = ocr_workflow.execute(license_plate_image)
    response = result[0].data
    assert isinstance(response, str)

    name = (ocr_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"ocr_{name}.png"))

def test_instructor_image_agent(instructor_image_workflow: Workflow, count_eggs_image):
    result, graph = instructor_image_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, EggCount)
    
    name = (instructor_image_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"instructor_image_{name}.png"))

def test_instructor_text_agent(instructor_text_workflow: Workflow, count_eggs_image):
    result, graph = instructor_text_workflow.execute(count_eggs_image)
    response = result[0].data
    assert isinstance(response, EggCount)  

    name = (instructor_text_workflow.steps[0].model.__class__.__name__)
    result[0].visualize().save(os.path.join(OUTPUT_DIR, f"instructor_text_{name}.png"))

import overeasy as ov
def pytest_sessionfinish(session, exitstatus):
    # Your function to run at the end of all tests
    print("All tests finished. Running final function.")
    # Add your function call here
    ov.logging.print_summary()