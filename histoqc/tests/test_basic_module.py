import openslide
from histoqc.BasicModule import getBasicStats


class FakeOsHandle:
    """Stands in for openslide.OpenSlide when only .properties is needed."""

    def __init__(self, properties):
        self.properties = properties


class FakeState(dict):
    """Minimal stand-in for BaseImage - just enough for getBasicStats."""

    def addToPrintList(self, name, val):
        self[name] = val


def test_get_basic_stats_reads_dicom_scanner_metadata():
    s = FakeState(filename='fake.dcm')
    s['os_handle'] = FakeOsHandle({
        'openslide.vendor': 'dicom',
        'dicom.Manufacturer': '3DHISTECH Kft.',
        'dicom.ManufacturerModelName': 'Pannoramic 1000',
    })

    getBasicStats(s, {})

    assert s['scanner_manufacturer'] == '3DHISTECH Kft.'
    assert s['scanner_model'] == 'Pannoramic 1000'


def test_get_basic_stats_scanner_metadata_na_for_non_dicom(svs_small):
    # Aperio (and every other non-DICOM OpenSlide backend, aside from the
    # legacy Leica SCN format handled separately below) has no equivalent to
    # dicom.Manufacturer/dicom.ManufacturerModelName, so these fields must
    # fall back to "NA" - the same default used for every other field in
    # getBasicStats - rather than None or raising.
    s = FakeState(filename='fake.svs')
    s['os_handle'] = openslide.OpenSlide(str(svs_small))

    getBasicStats(s, {})

    assert s['type'] == 'aperio'
    assert s['scanner_manufacturer'] == 'NA'
    assert s['scanner_model'] == 'NA'


def test_get_basic_stats_reads_leica_scn_device_model():
    # The older Leica SCN format (pre-dating Leica's 2012 acquisition of
    # Aperio) has no dicom.* properties, but does expose leica.device-model
    # from its own XML metadata - relevant only to historical .scn archives,
    # since every Leica scanner since the acquisition uses the aperio.*
    # namespace instead.
    s = FakeState(filename='fake.scn')
    s['os_handle'] = FakeOsHandle({
        'openslide.vendor': 'leica',
        'leica.device-model': 'SCN400',
    })

    getBasicStats(s, {})

    # No leica.manufacturer property exists to pair with leica.device-model,
    # so scanner_manufacturer still falls back to "NA" here - the "type"
    # column ("leica") already implies the manufacturer.
    assert s['scanner_manufacturer'] == 'NA'
    assert s['scanner_model'] == 'SCN400'


def test_get_basic_stats_prefers_dicom_manufacturer_model_over_leica():
    # Belt-and-braces: if a file somehow had both, the standard DICOM
    # properties should win over the legacy Leica-specific fallback.
    s = FakeState(filename='fake.dcm')
    s['os_handle'] = FakeOsHandle({
        'openslide.vendor': 'dicom',
        'dicom.ManufacturerModelName': 'Pannoramic 1000',
        'leica.device-model': 'SCN400',
    })

    getBasicStats(s, {})

    assert s['scanner_model'] == 'Pannoramic 1000'
