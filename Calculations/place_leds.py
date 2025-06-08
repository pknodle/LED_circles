import dataclasses

from kipy import KiCad
from math import pi, sin, cos, tan, atan2

from kipy.geometry import Vector2, Angle


@dataclasses.dataclass
class LEDLayout:
    lines: int
    leds_per_row: int
    diameter_steps_mm: float
    starting_diameter:float

    @property
    def leds_per_line_segment(self):
        return self.leds_per_row // 2

    @property
    def angle_step(self):
        return (2 * pi) / (2 * self.lines)

    def led_position_to_index(self, line_segment, position):

        if line_segment < self.lines:
            index_base = line_segment * 2 * self.leds_per_line_segment
        else:
            index_base = (line_segment % self.lines) * 2 * self.leds_per_line_segment
            index_base += self.leds_per_line_segment

        line_forward = line_segment % 2 == 0
        if line_forward:
            return index_base + position
        else:
            return index_base + self.leds_per_line_segment - position - 1

    def led_position_to_orientation(self, line_segment):
        #line_segment = line_segment % self.lines
        angle_rad = -self.angle_step * line_segment
        return Angle.from_degrees((180/pi) * angle_rad)

    def led_position_to_x_y(self, line_segment, position):
        angle = pi + self.angle_step * line_segment
        position_from_outside = self.leds_per_line_segment - position - 1
        radius = ((self.starting_diameter / 2) +
                  (self.diameter_steps_mm / 2) *  position_from_outside)
        return radius * cos(angle), radius * sin(angle)


if __name__=='__main__':

    kicad = KiCad()
    print(f"Connected to KiCad {kicad.get_version()}")

    board = KiCad().get_board()
    footprints = board.get_footprints()

    leds = {}

    for f in footprints:
        ref_text = f.reference_field.text.value
        if ref_text[0] == 'U' and f.definition.id.name == 'IN-PI55TAT':
            ref_number = int(ref_text[1:])
            leds[ref_number] = f
            print(f)

    # Now get a list of LEDs sorted by refdes
    sorted_leds = sorted(leds.items(), key=lambda led: led[0])
    sorted_leds = list(map(lambda led: led[1], sorted_leds))

    layout = LEDLayout(lines = 6,
                       leds_per_row = 12,
                       diameter_steps_mm = 14.5,
                       starting_diameter = 26)


    if layout.leds_per_row % 2 == 1:
        raise ValueError("There must be an even number of leds per row")
    # Each line is split into two segments.
    # This is to aid with the PCB layout.
    # The data traces goes half way from the outer edge to the center,
    # then the trace goes to the next line segment.
    # This way, the traces won't have to cross in the center.
    updates = set()
    for line_segment_index in range(layout.lines * 2):
        for position_index in range(layout.leds_per_row // 2):
            index = layout.led_position_to_index(line_segment_index, position_index)
            x_y = layout.led_position_to_x_y(line_segment_index, position_index)
            led_footprint = sorted_leds[index]
            led_footprint.position = Vector2.from_xy_mm(*x_y)
            led_footprint.orientation = layout.led_position_to_orientation(line_segment_index)
            print(f'{led_footprint.reference_field.text.value}: {index}')
            updates.add(led_footprint)
        print('---')
    board.update_items(updates)
