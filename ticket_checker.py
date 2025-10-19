import json
from typing import Set, List, Dict


class TicketExtractor:
    """Načítava a extrahuje ticket ID z JSON súborov."""

    def __init__(self, json_path: str):
        self.json_path = json_path

    def extract_ticket_ids(self) -> Set[str]:
        with open(self.json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        ticket_ids: Set[str] = set()
        for entry in data:
            ticket = entry.get("relationships", {}).get("ticket", {})
            ticket_id = ticket.get("id")
            if ticket_id:
                ticket_ids.add(ticket_id)

        return ticket_ids
    
    
    @staticmethod
    def from_data(data: List[Dict]) -> "TicketExtractorData":
        """Vytvorí pomocný objekt priamo z dát (bez čítania súboru)."""
        return TicketExtractorData(data)

    @staticmethod
    def _extract_from_list(data: List[Dict]) -> Set[str]:
        ticket_ids: Set[str] = set()
        for entry in data:
            ticket = entry.get("relationships", {}).get("ticket", {})
            ticket_id = ticket.get("id")
            if ticket_id:
                ticket_ids.add(ticket_id)
        return ticket_ids


class ReferenceTicketsLoader:
    """Načítava referenčné ticket ID zo súboru."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    def load(self) -> Set[str]:
        with open(self.filepath, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()
        return {line.strip() for line in lines if line.strip()}


class TicketComparator:
    """Porovnáva checkin ticket ID s referenčnými."""

    def __init__(self, checkin_tickets: Set[str], reference_tickets: Set[str]):
        self.checkin_tickets = checkin_tickets
        self.reference_tickets = reference_tickets

    def get_missing_tickets(self) -> Set[str]:
        return self.reference_tickets - self.checkin_tickets


class FileExporter:
    """Exportuje dáta do súborov."""

    @staticmethod
    def save_json(filepath: str, data) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def save_text(filepath: str, lines: Set[str]) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for line in sorted(lines):
                f.write(line + "\n")

class TicketExtractorData:
    """Pomocná trieda pre spracovanie dát v pamäti."""
    def __init__(self, data: List[Dict]):
        self.data = data

    def extract_ticket_ids(self) -> Set[str]:
        return TicketExtractor._extract_from_list(self.data)


def main():
    # záloha
    with open("checkin_entries.json", "r", encoding="utf-8") as f:
        checkin_data = json.load(f)
    FileExporter.save_json("all_checkins_backup.json", checkin_data)

    # načítanie údajov
    extractor = TicketExtractor("checkin_entries.json")
    loader = ReferenceTicketsLoader("reference_tickets_from_goout_app.txt")

    checkin_tickets = extractor.extract_ticket_ids()
    reference_tickets = loader.load()

    print(f"Načítaných záznamov z JSON: {len(checkin_tickets)}")
    print(f"Načítaných referenčných ticketov: {len(reference_tickets)}")

    # porovnanie
    comparator = TicketComparator(checkin_tickets, reference_tickets)
    missing_tickets = comparator.get_missing_tickets()

    print(f"\nChýbajúce ticket ID ({len(missing_tickets)}):")
    for ticket in sorted(missing_tickets):
        print(ticket)

    # uloženie výsledkov
    FileExporter.save_text("missing_tickets.txt", missing_tickets)
    print("\nHotovo! Výsledky uložené.")


if __name__ == "__main__":
    main()
