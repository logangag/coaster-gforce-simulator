from drafter import *
from dataclasses import dataclass
import math

set_website_title("Roller Coaster G-Force Simulator")
set_site_information(
    author="Logan Gagliardo",
    description="Create different coaster elements and simulate the forces applied to the rider.",
    sources="source",
    planning="Copy of CS1 Final Project 1_ Design.docx",
    links=["https://github.com/logangag/coaster-gforce-simulator"]
)
hide_debug_information()
set_website_framed(False)

# Fixed values used by the simulator
GRAVITY = 9.81
BRAKE_DURATION = 5.0

MAX_VERTICAL_G = 4.5
MIN_VERTICAL_G = -1.0
MAX_LATERAL_G = 1.5
MAX_FORWARD_G = 1.5


@dataclass
class TrackElement:
    name: str
    element_type: str
    parameters: dict[str, float]
    entry_speed: float
    vertical_g: float
    lateral_g: float


@dataclass
class State:
    coaster_name: str
    elements: list[TrackElement]
    current_element_type: str
    current_speed: float
    report: list[str]


# HOME PAGE
@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Roller Coaster G-Force Simulator"),
        "Build your own virtual roller coaster and see how its track elements affect G-forces.",
        "Coaster name:",
        TextBox("coaster_name", state.coaster_name),
        "Choose your first track element:",
        SelectBox("first_element", ["Launch", "90-degree Drop"]),
        Button("Start Building", "begin_coaster")
    ])


# CHOOSE THE FIRST ELEMENT
@route
def begin_coaster(state: State, coaster_name: str,
                  first_element: str) -> Page:
    state.coaster_name = coaster_name
    state.current_element_type = first_element
    state.elements = []
    state.current_speed = 0.0
    state.report = []

    if first_element == "Launch":
        return launch_page(state)
    else:
        return drop_page(state)


# LAUNCH CONFIGURATION PAGE
@route
def launch_page(state: State) -> Page:
    return Page(state, [
        Header("Configure Your Launch"),
        "Enter the launch acceleration in meters per second squared:",
        TextBox("acceleration", 10.0),
        "Enter how many seconds the launch lasts:",
        TextBox("duration", 3.0),
        Button("Add Launch", "save_launch")
    ])


# SAVE THE LAUNCH
@route
def save_launch(state: State, acceleration: float,
                duration: float) -> Page:

    entry_speed = state.current_speed
    forward_g = acceleration / GRAVITY

    new_speed = max(0.0, entry_speed + acceleration * duration)

    launch = TrackElement(
        "Launch",
        "Launch",
        {
            "acceleration": acceleration,
            "duration": duration,
            "forward_g": forward_g
        },
        entry_speed,
        1.0,
        0.0
    )

    state.elements.append(launch)
    state.current_speed = new_speed

    return element_selection_page(state)


# DROP CONFIGURATION PAGE
@route
def drop_page(state: State) -> Page:
    return Page(state, [
        Header("Configure Your 90-Degree Drop"),
        "Enter the vertical drop height in meters:",
        TextBox("drop_height", 30.0),
        "Enter the radius of the curve at the bottom in meters:",
        TextBox("curve_radius", 15.0),
        Button("Add Drop", "save_drop")
    ])


# SAVE THE DROP
@route
def save_drop(state: State, drop_height: float,
              curve_radius: float) -> Page:

    entry_speed = state.current_speed

    # Estimate speed using conservation of energy
    new_speed = math.sqrt(
        entry_speed ** 2 + 2 * GRAVITY * max(0.0, drop_height)
    )

    # Estimate vertical G-force at the bottom of the curve
    if curve_radius > 0:
        vertical_g = 1 + (new_speed ** 2 /
                          (curve_radius * GRAVITY))
    else:
        vertical_g = 0.0

    drop = TrackElement(
        "90-Degree Drop",
        "Drop",
        {
            "drop_height": drop_height,
            "curve_radius": curve_radius
        },
        entry_speed,
        vertical_g,
        0.0
    )

    state.elements.append(drop)
    state.current_speed = new_speed

    return element_selection_page(state)


# CHOOSE ADDITIONAL TRACK ELEMENTS
@route
def element_selection_page(state: State) -> Page:
    return Page(state, [
        Header("Build Your Coaster"),
        "Current coaster: " + state.coaster_name,
        "Current speed: " + str(round(state.current_speed, 2)) + " m/s",
        "Track elements added: " + str(len(state.elements)),
        "Choose your next track element:",
        SelectBox(
            "element_type",
            ["Vertical Loop", "Airtime Hill", "Banked Turn"]
        ),
        Button("Configure Element", "choose_element"),
        Button("Finish Coaster", "finish_track")
    ])


# SELECT AN ELEMENT
@route
def choose_element(state: State, element_type: str) -> Page:
    state.current_element_type = element_type
    return element_config_page(state)


# CONFIGURE AN ADDITIONAL ELEMENT
@route
def element_config_page(state: State) -> Page:
    if state.current_element_type == "Banked Turn":
        return Page(state, [
            Header("Configure Banked Turn"),
            "Enter the curve radius in meters:",
            TextBox("radius", 20.0),
            "Enter the bank angle in degrees:",
            TextBox("bank_angle", 30.0),
            Button("Add Element", "add_element_action")
        ])
    else:
        return Page(state, [
            Header("Configure " + state.current_element_type),
            "Enter the curve radius in meters:",
            TextBox("radius", 20.0),
            Button("Add Element", "add_element_action")
        ])


# ADD THE ELEMENT AND CALCULATE ITS G-FORCES
@route
def add_element_action(state: State, radius: float,
                       bank_angle: float = 0.0) -> Page:

    entry_speed = state.current_speed
    vertical_g = 1.0
    lateral_g = 0.0

    if radius <= 0:
        radius = 1.0

    centripetal_g = entry_speed ** 2 / (radius * GRAVITY)

    if state.current_element_type == "Vertical Loop":
        vertical_g = 1 + centripetal_g

    elif state.current_element_type == "Airtime Hill":
        vertical_g = 1 - centripetal_g

    elif state.current_element_type == "Banked Turn":
        lateral_g = centripetal_g * math.sin(
            math.radians(bank_angle)
        )

    element = TrackElement(
        state.current_element_type,
        state.current_element_type,
        {
            "radius": radius,
            "bank_angle": bank_angle
        },
        entry_speed,
        vertical_g,
        lateral_g
    )

    state.elements.append(element)

    return element_selection_page(state)


# FINISH THE COASTER AND AUTOMATICALLY ADD A BRAKE RUN
@route
def finish_track(state: State) -> Page:

    # The brake run is automatically added as the final element.
    entry_speed = state.current_speed
    deceleration = entry_speed / BRAKE_DURATION
    forward_g = -deceleration / GRAVITY

    brake_run = TrackElement(
        "Required Brake Run",
        "Brake Run",
        {
            "deceleration": deceleration,
            "duration": BRAKE_DURATION,
            "forward_g": forward_g
        },
        entry_speed,
        1.0,
        0.0
    )

    state.elements.append(brake_run)
    state.current_speed = 0.0

    return report_page(state)


# FINAL REPORT PAGE
@route
def report_page(state: State) -> Page:

    state.report = []

    state.report.append("Coaster: " + state.coaster_name)
    state.report.append(
        "Total track elements: " + str(len(state.elements))
    )
    state.report.append("")

    overall_safe = True

    # Loop through every track element and evaluate its G-forces.
    for element in state.elements:

        state.report.append(element.name)

        state.report.append(
            "Entry speed: " + str(round(element.entry_speed, 2))
            + " m/s"
        )

        state.report.append(
            "Vertical G-force: " + str(round(element.vertical_g, 2))
        )

        state.report.append(
            "Lateral G-force: " + str(round(element.lateral_g, 2))
        )

        # Check the vertical G-force limits.
        if (element.vertical_g > MAX_VERTICAL_G or
                element.vertical_g < MIN_VERTICAL_G):
            state.report.append("Vertical G-force: EXCEEDS PROGRAM LIMIT")
            overall_safe = False
        else:
            state.report.append("Vertical G-force: Within program limits")

        # Check the lateral G-force limit.
        if abs(element.lateral_g) > MAX_LATERAL_G:
            state.report.append("Lateral G-force: EXCEEDS PROGRAM LIMIT")
            overall_safe = False
        else:
            state.report.append("Lateral G-force: Within program limits")

        # Check the forward/backward G-force, if the element has one.
        forward_g = element.parameters.get("forward_g", 0.0)

        if abs(forward_g) > MAX_FORWARD_G:
            state.report.append("Forward/backward G-force: EXCEEDS PROGRAM LIMIT")
            overall_safe = False
        else:
            state.report.append("Forward/backward G-force: Within program limits")

        state.report.append("")

    if overall_safe:
        state.report.append("Overall Result: Within this program's thresholds.")
    else:
        state.report.append("Overall Result: Some elements exceed this program's thresholds.")

    return Page(state, [
        Header("Final Coaster Report"),
        Header(state.coaster_name, 2),
        "The following report evaluates each track element:",
        BulletedList(state.report),
        Button("Start a New Coaster", "restart_action")
    ])


# RESTART THE SIMULATOR
@route
def restart_action(state: State) -> Page:
    state.coaster_name = ""
    state.elements = []
    state.current_element_type = ""
    state.current_speed = 0.0
    state.report = []

    return index(state)


start_server(State(
    "",
    [],
    "",
    0.0,
    []
))
