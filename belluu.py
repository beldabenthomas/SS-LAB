import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Assembler function
def run_assembler(input_path, optab_path):
    locctr = 0
    symtab = {}
    intermediate_lines = []
    object_code_lines = []
    optab = {}
    program_name = None

    # Read the Opcode Table (OPTAB)
    with open(optab_path, 'r') as f:
        for line in f:
            mnemonic, machine_code = line.strip().split()
            optab[mnemonic] = machine_code

    # Pass 1: Process the input file, build SYMTAB and create intermediate file
    with open(input_path, 'r') as fin:
        for line in fin:
            line = line.strip().split()

            # Handle line format (either with or without label)
            if len(line) == 3:
                label, opcode, operand = line
            else:
                label = None
                opcode, operand = line

            # Handle START directive
            if opcode == 'START':
                locctr = int(operand, 16)  # Convert operand to hexadecimal
                program_name = label  # Save program name
                intermediate_lines.append(f"{locctr:04X}\t{label or ''}\t{opcode}\t{operand}")
                continue  # Skip to the next line after handling START

            # Add to intermediate file representation
            intermediate_lines.append(f"{locctr:04X}\t{label or ''}\t{opcode}\t{operand}")

            # Add label to SYMTAB if it's not a duplicate
            if label and label not in symtab:
                symtab[label] = locctr

            # Update LOCCTR based on instruction or directive
            if opcode in optab:
                locctr += 3  # Assuming all machine instructions take 3 bytes
            elif opcode == 'WORD':
                locctr += 3
            elif opcode == 'RESW':
                locctr += 3 * int(operand)  # RESW takes 3 bytes per word
            elif opcode == 'RESB':
                locctr += int(operand)  # RESB takes the size in bytes
            elif opcode == 'BYTE':
                if operand.startswith('C'):
                    locctr += len(operand) - 3  # Length of character constant
                elif operand.startswith('X'):
                    locctr += (len(operand) - 3) // 2  # Length of hex constant
            elif opcode == 'END':
                intermediate_lines.append(f"{locctr:04X}\t{label or ''}\t{opcode}\t{operand}")
                break

    # Pass 2: Generate Object Code using intermediate lines and SYMTAB
    starting_address = None
    text_records = []
    current_record = []
    current_length = 0

    for line in intermediate_lines:
        parts = line.strip().split('\t')

        if len(parts) == 4:
            locctr_str, label, opcode, operand = parts
            locctr = int(locctr_str, 16)  # Convert locctr back to int for calculations
        else:
            locctr_str, opcode, operand = parts
            label = None
            locctr = int(locctr_str, 16)  # Convert locctr back to int for calculations

        object_code = None

        # Generate object code for each instruction
        if opcode in optab:
            if operand in symtab:
                object_code = f"{optab[opcode]}{symtab[operand]:04X}"  # Opcode + Symbol Address
            else:
                object_code = f"{optab[opcode]}{int(operand):04X}"  # Opcode + Numeric Operand
        elif opcode == 'WORD':
            object_code = f"{int(operand):06X}"
        elif opcode == 'BYTE':
            if operand.startswith('C'):
                object_code = ''.join(f"{ord(c):02X}" for c in operand[2:-1])  # Convert chars to hex
            elif operand.startswith('X'):
                object_code = operand[2:-1]  # Remove 'X' and return hex value
        elif opcode in ['RESW', 'RESB', 'END']:
            continue  # No object code for these

        # Initialize starting address on START directive
        if starting_address is None and opcode == 'START':
            starting_address = locctr

        # Prepare text records
        if object_code:
            current_record.append(object_code)
            current_length += len(object_code) // 2  # Each object code is 2 characters per byte

            # If length exceeds 30 bytes, create a new text record
            if current_length > 30 or len(current_record) == 10:
                text_record = f"T^{starting_address:06X}^{current_length:02X} " + " ".join(current_record)
                text_records.append(text_record)
                current_record = []
                current_length = 0
                starting_address = locctr  # Set to current locctr for next record

    # If there are any remaining object codes to record
    if current_record:
        text_record = f"T^{starting_address:06X}^{current_length:02X} " + " ".join(current_record)
        text_records.append(text_record)

    # Generate the header record
    length = locctr - (starting_address if starting_address else 0)  # Calculate the length of the program
    header_record = f"H^{program_name}^{starting_address:06X}^{length:06X}"
    object_code_lines.append(header_record)  # Append header at the beginning

    # Add the end record
    object_code_lines.append(f"E^{starting_address:06X}")

    # Return both the intermediate representation, symbol table, and final object code
    return intermediate_lines, symtab, object_code_lines, text_records

# GUI Setup
def run_gui():
    def load_input_file():
        input_file_path.set(filedialog.askopenfilename(filetypes=[("Assembly Files", "*.asm"), ("All Files", "*.*")]))
        
    def load_optab_file():
        optab_file_path.set(filedialog.askopenfilename(filetypes=[("Opcode Table Files", "*.txt"), ("All Files", "*.*")]))
        
    def run_assembler_and_display():
        input_path = input_file_path.get()
        optab_path = optab_file_path.get()

        if not input_path or not optab_path:
            messagebox.showerror("Error", "Please select both input.asm and optab.txt files.")
            return

        try:
            intermediate_lines, symtab, object_code_lines, text_records = run_assembler(input_path, optab_path)

            # Clear text fields before outputting new data
            intermediate_text.delete(1.0, tk.END)
            symtab_text.delete(1.0, tk.END)
            object_code_text.delete(1.0, tk.END)

            # Display intermediate lines
            for line in intermediate_lines:
                intermediate_text.insert(tk.END, line + "\n")

            # Display symbol table
            for label, address in symtab.items():
                symtab_text.insert(tk.END, f"{label}\t{address:04X}\n")

            # Display object code with text records
            for line in object_code_lines:
                object_code_text.insert(tk.END, line + "\n")
            for line in text_records:
                object_code_text.insert(tk.END, line + "\n")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # GUI layout
    root = tk.Tk()
    root.title("---BELDA'S PASS1 AND PASS2 ASSEMBLER---")
    root.configure(bg='light yellow')  # Set background color to light yellow

    # Input file section
    tk.Label(root, text="INPUT FILE :", bg='light yellow').grid(row=0, column=0, padx=10, pady=5, sticky='e')
    input_file_path = tk.StringVar()
    tk.Entry(root, textvariable=input_file_path, width=50).grid(row=0, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=load_input_file, bg='light blue').grid(row=0, column=2, padx=10, pady=5)  # Light blue button

    # Opcode table file section
    tk.Label(root, text="OPCODE FILE:", bg='light yellow').grid(row=1, column=0, padx=10, pady=5, sticky='e')
    optab_file_path = tk.StringVar()
    tk.Entry(root, textvariable=optab_file_path, width=50).grid(row=1, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=load_optab_file, bg='light blue').grid(row=1, column=2, padx=10, pady=5)  # Light blue button

    # Run button
    tk.Button(root, text="Run Assembler", command=run_assembler_and_display, bg='light green').grid(row=2, column=0, columnspan=3, padx=10, pady=10)  # Light green button

    # Intermediate output section
    tk.Label(root, text="Intermediate Code:", bg='light yellow').grid(row=3, column=0, sticky='w')
    intermediate_text = scrolledtext.ScrolledText(root, width=60, height=10)
    intermediate_text.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

    # Symbol table section
    tk.Label(root, text="SymTab:", bg='light yellow').grid(row=5, column=0, sticky='w')
    symtab_text = scrolledtext.ScrolledText(root, width=30, height=10)
    symtab_text.grid(row=6, column=0, columnspan=1, padx=10, pady=5)

    # Object code output section
    tk.Label(root, text="Object Code:", bg='light yellow').grid(row=5, column=1, sticky='w')
    object_code_text = scrolledtext.ScrolledText(root, width=60, height=10)
    object_code_text.grid(row=6, column=1, columnspan=2, padx=10, pady=5)

    root.mainloop()

# Start GUI
if __name__ == "__main__":
    run_gui()
