from struct import unpack
from typing import TypedDict, Any


class ASB(TypedDict, total=False):
    raw: bytes
    version: int
    # 3
    offline_by_sw: bool
    cover_open: bool
    online: bool
    drawer_open: bool
    etb: bool
    # 4
    head_overheat: bool
    irrecoverable_error: bool
    auto_cutter_error: bool
    mechanical_error: bool
    head_themistor_error: bool
    # 5
    black_mark_error: bool
    paper_jam_error: bool
    voltage_error: bool
    # 6
    paper_position_error: bool
    paper_end: bool
    paper_near_end_inner: bool
    paper_near_end_outer: bool
    # 7
    paper_hold_sensor: bool
    # 8
    etb_counter: int
    # 10
    pcb_overheat: bool
    drawer_open_error: bool
    flash_access_error: bool
    eeprom_access_error: bool
    sram_access_error: bool
    # 11
    pcb_themistor_error: bool
    sensor_adjustment_error: bool
    printer_unit_open: bool
    spooler_buffer_full: bool
    # 12
    interface: int
    # 13:
    drawer_op_method: bool
    drawer_status: bool
    # 15
    external_1_connected: bool
    external_2_connected: bool
    # 16
    part_replace_notify: bool
    clean_notify: bool
    paper_width: int


def _bit(byte: int, bit: int) -> bool:
    return bool(byte & (1 << bit))

def parse_asb(asb: bytes) -> tuple[ASB, dict[str, Any] | None]:
    res = {"raw": asb}
    header1 = asb[0]
    size = ((header1 & 0b1110) >> 1) | ((header1 & 0b1100000) >> 2)
    print(f"{size=}")
    header2 = asb[1]
    version = ((header2 & 0b1110) >> 1) | ((header2 & 0b100000) >> 2)
    res["version"] = version
    print(f"{version=}")
    extension = _bit(header2, 7)
    print(f"{extension=}")
    if size >= 3:
        res["offline_by_sw"] = _bit(asb[2], 6)
        res["cover_open"] = _bit(asb[2], 5)
        res["online"] = not _bit(asb[2], 3)
        res["drawer_open"] = _bit(asb[2], 2)
        res["etb"] = _bit(asb[2], 1)
    if size >= 4:
        res["head_overheat"] = _bit(asb[3], 6)
        res["irrecoverable_error"] = _bit(asb[3], 5)
        res["auto_cutter_error"] = _bit(asb[3], 3)
        res["mechanical_error"] = _bit(asb[3], 2)
        res["head_themistor_error"] = _bit(asb[3], 1)
    if size >= 5:
        res["black_mark_error"] = _bit(asb[4], 3)
        res["paper_jam_error"] = _bit(asb[4], 2)
        res["voltage_error"] = _bit(asb[4], 1)
    if size >= 6:
        res["paper_position_error"] = _bit(asb[5], 5)
        res["paper_end"] = _bit(asb[5], 3)
        res["paper_near_end_inner"] = _bit(asb[5], 2)
        res["paper_near_end_outer"] = _bit(asb[5], 1)
    if size >= 7:
        res["paper_hold_sensor"] = _bit(asb[6], 1)
    if size >= 8:
        res["etb_counter"] = ((asb[7] & 0b1110) >> 1) | ((asb[7] & 0b1100000) >> 2)
    if size >= 10:
        res["pcb_overheat"] = _bit(asb[9], 6)
        res["drawer_open_error"] = _bit(asb[9], 5)
        res["flash_access_error"] = _bit(asb[9], 3)
        res["eeprom_access_error"] = _bit(asb[9], 2)
        res["sram_access_error"] = _bit(asb[9], 1)
    if size >= 11:
        res["pcb_themistor_error"] = _bit(asb[10], 6)
        res["sensor_adjustment_error"] = _bit(asb[10], 5)
        res["printer_unit_open"] = _bit(asb[10], 3)
        res["spooler_buffer_full"] = _bit(asb[10], 2)
    if size >= 12:
        res["interface"] = ((asb[11] & 0b1110) >> 1) | ((asb[11] & 0b1100000) >> 2)
    if size >= 13:
        res["drawer_op_method"] = _bit(asb[12], 6)
        res["drawer_status"] = _bit(asb[12], 5)
    if size >= 15:
        res["external_1_connected"] = _bit(asb[14], 6)
        res["external_2_connected"] = _bit(asb[14], 5)
    if size >= 16:
        res["part_replace_notify"] = _bit(asb[15], 6)
        res["clean_notify"] = _bit(asb[15], 5)
        if (width := (asb[15] & 0b1110) >> 1) == 0:
            res["paper_width"] = 80
        elif width == 1:
            res["paper_width"] = 58
        elif width == 2:
            res["paper_width"] = 40
        elif width == 3:
            res["paper_width"] = 25
    extra = None
    if extension:
        status_length = unpack("<H", asb[size:size+2])[0]
        if status_length > 0:
            status_data = asb[size+2:size+2+status_length]
            status_type = status_data[0:2]
            value = status_data[6:-1]
            if status_type == b"11":
                extra = {"printer_version": value.decode()[4:-2]}
            else:
                extra = {status_type.decode(): value}
    return res, extra

