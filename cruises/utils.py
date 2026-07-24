def get_seat_layout():
    """
    Returns a list of tuples: (row_index, seat_number, row_label, position)
    matching the exact Rameshwaram Cruise 60-seat layout (window-aligned):
    R1: 1 2 3 - 4 5 6 (Left: positions 1,2,3; Right: positions 7,8,9)
    R2: 7 8 9 10 - 11 12 13 (Left: 1,2,3,4; Right: 7,8,9)
    R3: 14 15 16 17 - 18 19 20 (Left: 1,2,3,4; Right: 7,8,9)
    R4: 21 22 23 24 - 25 26 27 28 (Left: 1,2,3,4; Right: 6,7,8,9)
    R5: 29 30 31 32 - 33 34 35 36 (Left: 1,2,3,4; Right: 6,7,8,9)
    R6: 37 38 39 40 - 41 42 43 44 (Left: 1,2,3,4; Right: 6,7,8,9)
    R7: 45 46 47 48 - 49 50 51 52 (Left: 1,2,3,4; Right: 6,7,8,9)
    R8: 53 54 55 56 - 57 58 59 60 (Left: 1,2,3,4; Right: 6,7,8,9)
    """
    layout = []
    # Row 1
    # Left: 1, 2, 3 (positions 1, 2, 3)
    # Right: 4, 5, 6 (positions 7, 8, 9)
    layout.extend([
        (1, "1", "R1", 1), (1, "2", "R1", 2), (1, "3", "R1", 3),
        (1, "4", "R1", 7), (1, "5", "R1", 8), (1, "6", "R1", 9)
    ])
    # Row 2
    # Left: 7, 8, 9, 10 (positions 1, 2, 3, 4)
    # Right: 11, 12, 13 (positions 7, 8, 9)
    layout.extend([
        (2, "7", "R2", 1), (2, "8", "R2", 2), (2, "9", "R2", 3), (2, "10", "R2", 4),
        (2, "11", "R2", 7), (2, "12", "R2", 8), (2, "13", "R2", 9)
    ])
    # Row 3
    # Left: 14, 15, 16, 17 (positions 1, 2, 3, 4)
    # Right: 18, 19, 20 (positions 7, 8, 9)
    layout.extend([
        (3, "14", "R3", 1), (3, "15", "R3", 2), (3, "16", "R3", 3), (3, "17", "R3", 4),
        (3, "18", "R3", 7), (3, "19", "R3", 8), (3, "20", "R3", 9)
    ])
    # Rows 4 to 8
    # Left: positions 1, 2, 3, 4
    # Right: positions 6, 7, 8, 9
    seat_counter = 21
    for r in range(4, 9):
        row_label = f"R{r}"
        # Left side (4 seats)
        for pos in range(1, 5):
            layout.append((r, str(seat_counter), row_label, pos))
            seat_counter += 1
        # Right side (4 seats)
        for pos in range(6, 10):
            layout.append((r, str(seat_counter), row_label, pos))
            seat_counter += 1
    return layout
