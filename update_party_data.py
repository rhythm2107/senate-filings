import sqlite3

# Provided senators data.
senators_data = [
    (1, "Jim Banks", "Indiana", "Republican"),
    (2, "John Boozman", "Arkansas", "Republican"),
    (3, "Shelley Moore Capito", "West Virginia", "Republican"),
    (4, "Dave McCormick", "Pennsylvania", "Republican"),
    (5, "Richard Blumenthal", "Connecticut", "Democratic"),
    (6, "Rick Scott", "Florida", "Republican"),
    (7, "Markwayne Mullin", "Oklahoma", "Republican"),
    (8, "Ashley Moody", "Florida", "Republican"),
    (9, "Ron Wyden", "Oregon", "Democratic"),
    (10, "Tommy Tuberville", "Alabama", "Republican"),
    (11, "John Fetterman", "Pennsylvania", "Democratic"),
    (12, "Marco Rubio", "Florida", "Republican"),
    (13, "Bill Hagerty", "Tennessee", "Republican"),
    (14, "Jerry Moran", "Kansas", "Republican"),
    (15, "Sheldon Whitehouse", "Rhode Island", "Democratic"),
    (16, "Mitch McConnell", "Kentucky", "Republican"),
    (17, "Tom Carper", "Delaware", "Democratic"),
    (18, "Tina Smith", "Minnesota", "Democratic"),
    (19, "Gary Peters", "Michigan", "Democratic"),
    (20, "Mark Warner", "Virginia", "Democratic"),
    (21, "John Hickenlooper", "Colorado", "Democratic"),
    (22, "Susan M. Collins", "Maine", "Republican"),
    (23, "Katie Britt", "Alabama", "Republican"),
    (24, "Lindsey Graham", "South Carolina", "Republican"),
    (25, "Ted Cruz", "Texas", "Republican"),
    (27, "Chris Coons", "Delaware", "Democratic"),
    (28, "Dan Sullivan", "Alaska", "Republican"),
    (29, "Joe Manchin", "West Virginia", "Democratic"),
    (30, "JD Vance", "Ohio", "Republican"),
    (31, "Pete Ricketts", "Nebraska", "Republican"),
    (32, "Roger Marshall", "Kansas", "Republican"),
    (33, "Thom Tillis", "North Carolina", "Republican"),
    (34, "Michael Bennet", "Colorado", "Democratic"),
    (35, "Tammy Duckworth", "Illinois", "Democratic"),
    (36, "Roy Blunt", "Missouri", "Republican"),
    (37, "Maria Cantwell", "Washington", "Democratic"),
    (38, "Jacky Rosen", "Nevada", "Democratic"),
    (39, "Pat Toomey", "Pennsylvania", "Republican"),
    (40, "Deb Fischer", "Nebraska", "Republican"),
    (41, "John Thune", "South Dakota", "Republican"),
    (42, "Dianne Feinstein", "California", "Democratic"),
    (43, "Cynthia Lummis", "Wyoming", "Republican"),
    (44, "Mark Kelly", "Arizona", "Democratic"),
    (45, "John Hoeven", "North Dakota", "Republican"),
    (46, "Rand Paul", "Kentucky", "Republican"),
    (47, "Mike Rounds", "South Dakota", "Republican"),
    (48, "Richard Burr", "North Carolina", "Republican"),
    (49, "David Perdue", "Georgia", "Republican"),
    (50, "Jim Inhofe", "Oklahoma", "Republican"),
    (51, "Pat Roberts", "Kansas", "Republican"),
    (52, "Bill Cassidy", "Louisiana", "Republican"),
    (53, "Kelly Loeffler", "Georgia", "Republican"),
    (54, "Tim Kaine", "Virginia", "Democratic"),
    (55, "Jeanne Shaheen", "New Hampshire", "Democratic"),
    (56, "Ron Johnson", "Wisconsin", "Republican"),
    (57, "Roger Wicker", "Mississippi", "Republican"),
    (58, "Lamar Alexander", "Tennessee", "Republican"),
    (59, "John Neely Kennedy", "Louisiana", "Republican"),
    (60, "Tom Udall", "New Mexico", "Democratic"),
    (62, "Steve Daines", "Montana", "Republican"),
    (63, "John Barrasso", "Wyoming", "Republican"),
    (64, "Bob Casey Jr.", "Pennsylvania", "Democratic"),
    (65, "Robert Jones Portman", "Ohio", "Republican"),
    (66, "Ben Cardin", "Maryland", "Democratic"),
    (68, "Mike Crapo", "Idaho", "Republican"),
    (69, "Patty Murray", "Washington", "Democratic"),
    (70, "Chris Van Hollen", "Maryland", "Democratic"),
    (71, "John Cornyn", "Texas", "Republican"),
    (74, "Cory Booker", "New Jersey", "Democratic"),
    (76, "Jack Reed", "Rhode Island", "Democratic"),
    (77, "Angus King", "Maine", "Independent (Caucuses with Democrats)"),
    (78, "Dean Heller", "Nevada", "Republican"),
    (79, "Thad Cochran", "Mississippi", "Republican"),
    (80, "John McCain", "Arizona", "Republican"),
    (83, "Claire McCaskill", "Missouri", "Democratic"),
    (84, "Jeff Sessions", "Alabama", "Republican"),
    (86, "Mike Enzi", "Wyoming", "Republican"),
    (88, "Jeff Flake", "Arizona", "Republican"),
    (89, "Orrin Hatch", "Utah", "Republican"),
    (90, "Elizabeth Warren", "Massachusetts", "Democratic"),
    (91, "Richard Shelby", "Alabama", "Republican"),
]

def update_senators_table(db_filename):
    """
    Connects to the specified SQLite database and updates the senators table.
    For each entry in senators_data, if a row exists in the senators table with
    the same senator_id and canonical_full_name, the script updates the state and
    party fields.
    """
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    
    for senator in senators_data:
        senator_id, canonical_full_name, state, party = senator
        # Check if a senator with matching senator_id and canonical_full_name exists.
        c.execute("""
            SELECT senator_id FROM senators
            WHERE senator_id = ? AND canonical_full_name = ?
        """, (senator_id, canonical_full_name))
        result = c.fetchone()
        
        if result:
            # Update state and party if the record is found.
            c.execute("""
                UPDATE senators
                SET state = ?, party = ?
                WHERE senator_id = ? AND canonical_full_name = ?
            """, (state, party, senator_id, canonical_full_name))
            print(f"Updated {canonical_full_name} (ID: {senator_id})")
        else:
            print(f"Senator {canonical_full_name} (ID: {senator_id}) not found in senators table.")
    
    conn.commit()
    conn.close()
    print("Senators table update completed.")

if __name__ == "__main__":
    # Replace 'your_database.sqlite' with the path to your SQLite database file.
    db_filename = "filings.db"
    update_senators_table(db_filename)
