def set_routes(self):

    # user interface routes
    self.app.add_url_rule("/", "root", self.root)
    self.app.add_url_rule("/log", "log", self.log, methods=["GET", "POST"])
    self.app.add_url_rule("/reg", "reg", self.reg, methods=["GET", "POST"])
    self.app.add_url_rule("/reg-2", "reg-2", self.reg2, methods=["GET", "POST"])
    self.app.add_url_rule("/rec", "rec", self.rec, methods=["GET", "POST"])
    self.app.add_url_rule("/rec-2", "rec-2", self.rec2, methods=["GET", "POST"])
    self.app.add_url_rule("/mic", "mic", self.mic, methods=["GET", "POST"])
    self.app.add_url_rule("/acerca", "acerca", self.acerca)
    self.app.add_url_rule("/logout", "logout", self.logout)

    # dashboard routes
    # self.app.add_url_rule("/dashboard", "dashboard", self.dash)
    self.app.add_url_rule("/wvpeagu2d27l6v7b", "dashboard", self.dash)
    self.app.add_url_rule("/data", "get_data", self.get_data)
    self.app.add_url_rule(
        "/registros",
        endpoint="registros",
        view_func=self.registros,
        methods=["POST"],
    )
    self.app.add_url_rule(
        "/crear_mensajes",
        endpoint="crear_mensajes",
        view_func=self.launch_gather_comm,
        methods=["POST"],
    )
    self.app.add_url_rule(
        "/enviar_mensajes",
        endpoint="enviar_mensajes",
        view_func=self.launch_gather_send,
        methods=["POST"],
    )
    self.app.add_url_rule(
        "/solo_enviar_mensajes",
        endpoint="solo_enviar_mensajes",
        view_func=self.launch_gather_only_send,
        methods=["POST"],
    )
    self.app.add_url_rule(
        "/redirect",
        endpoint="redirect",
        view_func=self.redir,
        methods=["POST", "GET"],
    )

    # redirect route (OAuth2)
    self.app.add_url_rule("/redir", "redir", self.redir)


def set_config(self):
    self.app.config["SECRET_KEY"] = "sdlkfjsdlojf3r49tgf8"
    self.app.config["TEMPLATES_AUTO_RELOAD"] = True
