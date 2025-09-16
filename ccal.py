#!/usr/bin/env python3
import sys
import os
import json
import locale
from datetime import date, datetime, timedelta
import calendar

APP_NAME = "CCAL"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ccal")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


# Windows curses support
try:
	of_import_error = None
	import curses
	import curses.textpad
except Exception as _exc:  # pragma: no cover
	curses = None
	of_import_error = _exc


locale.setlocale(locale.LC_ALL, "")
calendar.setfirstweekday(calendar.MONDAY)


def ensure_dirs() -> None:
	if not os.path.isdir(CONFIG_DIR):
		os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
	ensure_dirs()
	if os.path.isfile(CONFIG_PATH):
		try:
			with open(CONFIG_PATH, "r", encoding="utf-8") as f:
				data = json.load(f)
				return data if isinstance(data, dict) else {}
		except Exception:
			return {}
	return {}


def save_config(cfg: dict) -> None:
	ensure_dirs()
	try:
		with open(CONFIG_PATH, "w", encoding="utf-8") as f:
			json.dump(cfg, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


class Theme:
	COLOR_DEFAULT = 1
	COLOR_HEADER = 2
	COLOR_DIM = 3
	COLOR_TODAY = 4
	COLOR_SELECTED = 5
	COLOR_STATUS = 6
	COLOR_HELP = 7
	COLOR_WEEKEND = 8

	@staticmethod
	def init_colors() -> None:
		curses.start_color()
		curses.use_default_colors()
		curses.init_pair(Theme.COLOR_DEFAULT, curses.COLOR_WHITE, -1)
		curses.init_pair(Theme.COLOR_HEADER, curses.COLOR_CYAN, -1)
		curses.init_pair(Theme.COLOR_DIM, curses.COLOR_BLACK, -1)
		curses.init_pair(Theme.COLOR_TODAY, curses.COLOR_GREEN, -1)
		curses.init_pair(Theme.COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW)
		curses.init_pair(Theme.COLOR_STATUS, curses.COLOR_BLACK, curses.COLOR_CYAN)
		curses.init_pair(Theme.COLOR_HELP, curses.COLOR_YELLOW, -1)
		curses.init_pair(Theme.COLOR_WEEKEND, curses.COLOR_MAGENTA, -1)


class CalendarApp:
	def __init__(self, stdscr) -> None:
		self.stdscr = stdscr
		self.cfg = load_config()
		today = date.today()
		self.current_year = today.year
		self.current_month = today.month
		self.selected_day = today.day
		self.view_mode = "month"  # "month" | "week"
		self.first_weekday = 0 if self.cfg.get("first_weekday", "mon") == "mon" else 6
		self.status = "Use arrows/PgUp/PgDn, T=Today, W=Week start, V=View"
		self.resize()

	def resize(self) -> None:
		self.max_y, self.max_x = self.stdscr.getmaxyx()

	# ----- Safe drawing helpers -----
	def safe_addnstr(self, y: int, x: int, s: str, n: int, attr: int | None = None) -> None:
		if self.max_x <= 0 or self.max_y <= 0:
			return
		if y < 0 or y >= self.max_y or x < 0 or x >= self.max_x:
			return
		if n <= 0:
			return
		n = min(n, self.max_x - x)
		if n <= 0:
			return
		try:
			if attr is None:
				self.stdscr.addnstr(y, x, s, n)
			else:
				self.stdscr.addnstr(y, x, s, n, attr)
		except Exception:
			pass

	def can_draw_full(self) -> bool:
		return self.max_x >= 36 and self.max_y >= 10

	# ----- Model helpers -----
	def clamp_selection(self) -> None:
		last_day = calendar.monthrange(self.current_year, self.current_month)[1]
		if self.selected_day < 1:
			self.selected_day = 1
		if self.selected_day > last_day:
			self.selected_day = last_day

	def move_month(self, delta: int) -> None:
		y, m = self.current_year, self.current_month
		m += delta
		while m < 1:
			m += 12
			y -= 1
		while m > 12:
			m -= 12
			y += 1
		self.current_year = max(1, min(9999, y))
		self.current_month = m
		self.clamp_selection()

	def move_year(self, delta: int) -> None:
		self.current_year = max(1, min(9999, self.current_year + delta))
		self.clamp_selection()

	def move_selection(self, days: int) -> None:
		try:
			base = date(self.current_year, self.current_month, self.selected_day)
		except ValueError:
			self.clamp_selection()
			base = date(self.current_year, self.current_month, self.selected_day)
		new_date = base + timedelta(days=days)
		self.current_year, self.current_month, self.selected_day = new_date.year, new_date.month, new_date.day

	def go_today(self) -> None:
		t = date.today()
		self.current_year, self.current_month, self.selected_day = t.year, t.month, t.day

	def toggle_week_start(self) -> None:
		if self.first_weekday == 0:
			self.first_weekday = 6
			self.status = "Week starts on Sunday"
		else:
			self.first_weekday = 0
			self.status = "Week starts on Monday"
		calendar.setfirstweekday(self.first_weekday)
		self.cfg["first_weekday"] = "mon" if self.first_weekday == 0 else "sun"
		save_config(self.cfg)

	# ----- View -----
	def draw_header(self) -> None:
		title = f"{calendar.month_name[self.current_month]} {self.current_year}"
		help_hint = "[ Arrows: Day | PgUp/PgDn: Month | T: Today | W: Week start | V: View ]"
		line = title.center(self.max_x)
		self.stdscr.attron(curses.color_pair(Theme.COLOR_HEADER) | curses.A_BOLD)
		self.safe_addnstr(0, 0, line, len(line))
		self.stdscr.attroff(curses.color_pair(Theme.COLOR_HEADER) | curses.A_BOLD)
		if self.max_y > 2:
			self.stdscr.attron(curses.color_pair(Theme.COLOR_HELP))
			self.safe_addnstr(1, 0, help_hint[: self.max_x], min(len(help_hint), self.max_x))
			self.stdscr.attroff(curses.color_pair(Theme.COLOR_HELP))

	def draw_status(self) -> None:
		if self.max_y <= 2:
			return
		bar = (" " + (self.status or "")).ljust(self.max_x)
		self.stdscr.attron(curses.color_pair(Theme.COLOR_STATUS))
		self.safe_addnstr(self.max_y - 1, 0, bar, len(bar))
		self.stdscr.attroff(curses.color_pair(Theme.COLOR_STATUS))

	def draw_month_view(self) -> None:
		calendar.setfirstweekday(self.first_weekday)
		cal = calendar.Calendar(firstweekday=self.first_weekday)
		weeks = cal.monthdatescalendar(self.current_year, self.current_month)
		start_row = 3
		day_names = [calendar.day_abbr[(i % 7)] for i in range(self.first_weekday, self.first_weekday + 7)]
		header = " ".join([f"{n[:2].capitalize():>3}" for n in day_names])
		self.stdscr.attron(curses.A_BOLD)
		self.safe_addnstr(start_row, 2, header, max(0, min(len(header), self.max_x - 4)))
		self.stdscr.attroff(curses.A_BOLD)
		row = start_row + 1
		today = date.today()

		for week in weeks:
			if row >= self.max_y - 1:
				break
			col = 2
			for d in week:
				if col >= self.max_x - 2:
					break
				is_this_month = (d.month == self.current_month)
				text = f"{d.day:2d}"
				attr = curses.color_pair(Theme.COLOR_DEFAULT)
				if d.weekday() >= 5:
					attr = curses.color_pair(Theme.COLOR_WEEKEND)
				if not is_this_month:
					attr = curses.color_pair(Theme.COLOR_DIM)
				if d == today:
					attr = curses.color_pair(Theme.COLOR_TODAY) | curses.A_BOLD
				if (d.year, d.month, d.day) == (self.current_year, self.current_month, self.selected_day):
					attr = curses.color_pair(Theme.COLOR_SELECTED) | curses.A_BOLD
				self.safe_addnstr(row, col, text, 2, attr)
				col += 4
			row += 1

	def draw_week_view(self) -> None:
		calendar.setfirstweekday(self.first_weekday)
		base = date(self.current_year, self.current_month, self.selected_day)
		start = base - timedelta(days=(base.weekday() - (0 if self.first_weekday == 0 else 6)) % 7)
		today = date.today()
		start_row = 3
		self.stdscr.attron(curses.A_BOLD)
		self.safe_addnstr(start_row, 2, "Week view", max(0, min(self.max_x - 4, len("Week view"))))
		self.stdscr.attroff(curses.A_BOLD)
		row = start_row + 1
		for i in range(7):
			if row >= self.max_y - 1:
				break
			d = start + timedelta(days=i)
			label = f"{calendar.day_name[d.weekday()][:3].capitalize()} {d.isoformat()}"
			attr = curses.color_pair(Theme.COLOR_DEFAULT)
			if d.weekday() >= 5:
				attr = curses.color_pair(Theme.COLOR_WEEKEND)
			if d == today:
				attr = curses.color_pair(Theme.COLOR_TODAY) | curses.A_BOLD
			if (d.year, d.month, d.day) == (self.current_year, self.current_month, self.selected_day):
				attr = curses.color_pair(Theme.COLOR_SELECTED) | curses.A_BOLD
			self.safe_addnstr(row, 2, label, max(0, min(self.max_x - 4, len(label))), attr)
			row += 1

	def draw(self) -> None:
		self.stdscr.erase()
		self.resize()
		if not self.can_draw_full():
			msg = "Resize terminal (min 36x10)"
			self.safe_addnstr(0, 0, msg[: self.max_x], min(len(msg), self.max_x))
			self.stdscr.refresh()
			return
		self.draw_header()
		if self.view_mode == "month":
			self.draw_month_view()
		else:
			self.draw_week_view()
		self.draw_status()
		self.stdscr.refresh()

	# ----- Input helpers -----
	def prompt(self, title: str, initial: str = "") -> str | None:
		if not self.can_draw_full():
			return None
		h, w = 3, max(20, min(60, len(title) + 20))
		y = max(2, (self.max_y - h) // 2)
		x = max(2, (self.max_x - w) // 2)
		try:
			win = curses.newwin(h, w, y, x)
		except Exception:
			return None
		win.box()
		try:
			win.addnstr(0, 2, f" {title} ", w - 4)
		except Exception:
			pass
		tb = curses.newwin(1, w - 4, y + 1, x + 2)
		tb.addstr(0, 0, initial)
		curses.curs_set(1)
		textpad = curses.textpad.Textbox(tb)
		self.stdscr.refresh()
		try:
			text = textpad.edit().strip()
		except Exception:
			text = None
		curses.curs_set(0)
		return text if text else None

	# ----- Event loop -----
	def handle_key(self, ch: int) -> bool:
		# True -> continue, False -> quit
		if ch in (ord("q"), ord("Q")):
			return False
		if ch in (ord("t"), ord("T")):
			self.go_today()
			self.status = "Today"
			return True
		if ch in (ord("w"), ord("W")):
			self.toggle_week_start()
			return True
		if ch in (ord("v"), ord("V")):
			self.view_mode = "week" if self.view_mode == "month" else "month"
			self.status = f"View: {self.view_mode}"
			return True
		if ch in (curses.KEY_LEFT, ord("h")):
			self.move_selection(-1)
			return True
		if ch in (curses.KEY_RIGHT, ord("l")):
			self.move_selection(1)
			return True
		if ch in (curses.KEY_UP, ord("k")):
			self.move_selection(-7)
			return True
		if ch in (curses.KEY_DOWN, ord("j")):
			self.move_selection(7)
			return True
		if ch == curses.KEY_NPAGE:  # PgDn
			self.move_month(1)
			self.status = "Next month"
			return True
		if ch == curses.KEY_PPAGE:  # PgUp
			self.move_month(-1)
			self.status = "Previous month"
			return True
		if ch == curses.KEY_RESIZE:
			self.resize()
			return True
		return True


def curses_main(stdscr) -> int:
	curses.curs_set(0)
	stdscr.nodelay(False)
	stdscr.keypad(True)
	Theme.init_colors()

	app = CalendarApp(stdscr)
	while True:
		app.draw()
		ch = stdscr.getch()
		if not app.handle_key(ch):
			break
	return 0


def run() -> int:
	if curses is None:
		print("This app requires curses for colorful interactive mode. On Windows: pip install windows-curses")
		if of_import_error is not None:
			print(f"Import error: {of_import_error}")
		return 1
	return curses.wrapper(curses_main)


if __name__ == "__main__":
	try:
		sys.exit(run())
	except Exception as exc:
		print(f"Error: {exc}")
		sys.exit(1)
