from src.services.api.api_integrator import ApiIntegrator


class ControllerImage:
    def __init__(self, integrator: ApiIntegrator):
        self._integrator = integrator
