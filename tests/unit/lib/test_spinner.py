from life.lib.spinner import Spinner


def test_spinner_init():
    spinner = Spinner()

    assert spinner.persona == "roast"
    assert spinner.stop_event is not None


def test_spinner_init_with_persona():
    spinner = Spinner(persona="pepper")

    assert spinner.persona == "pepper"


def test_spinner_start_stop():
    spinner = Spinner()

    spinner.start()
    assert spinner.thread is not None

    spinner.stop()
    spinner.thread.join(timeout=1)


def test_spinner_personas():
    for persona in ["roast", "pepper", "kim"]:
        spinner = Spinner(persona=persona)
        assert spinner.persona == persona
