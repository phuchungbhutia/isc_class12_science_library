#!/usr/bin/env python3
"""
Generates valid benchmark PDF-equivalent test documents into the repository
to test Phase 3 auditing, hashing, and Phase 4 question extraction.
"""

import os

BASE_DIR = "./isc_class12_science_library"

# 1. Physics Benchmark Document Text (CISCE Pattern)
PHYSICS_2026_TEXT = """%PDF-1.4 Benchmark Simulated Document
COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS
ISC CLASS XII SPECIMEN QUESTION PAPER 2026
PHYSICS (PAPER 1 - THEORY)
Maximum Marks: 70
Time Allowed: Three hours

SECTION A (14 Marks)
Question 1
(i) The electric flux through a closed Gaussian surface depends only on: [1]
(a) the shape of the surface
(b) the size of the surface
(c) the net charge enclosed
(d) the permittivity of the surrounding medium outside

Question 2
Assertion (A): Core of a transformer is laminated to reduce eddy current losses.
Reason (R): Narrow lamination strips reduce the continuous loop path for circulating currents. [1]
(a) Both A and R are true and R is the correct explanation of A.
(b) Both A and R are true but R is not the correct explanation of A.
(c) A is true but R is false.
(d) A is false but R is true.

SECTION B (14 Marks)
Question 3
Derive an expression for the drift velocity of free electrons in a metallic conductor in terms of relaxation time. [2]

Question 4
State Huygens' principle. Use it to construct a refracted wavefront when a plane wave is incident on a denser medium. [2]

Question 5
Two capacitors of capacitance 3 uF and 6 uF are connected in series across a 120 V DC supply. Calculate the potential difference across the 3 uF capacitor. [2]

SECTION C (27 Marks)
Question 6
Draw a neat labeled circuit diagram of a Wheatstone bridge. Derive the balanced condition using Kirchhoff's laws. [3]

Question 7
An alternating voltage given by V = 282 sin(100 pi t) is connected across a series LCR circuit with R = 30 ohm, L = 0.4 H, and C = 25 uF. Determine:
(i) the resonance frequency,
(ii) the impedance at resonance,
(iii) the power factor. [3]

SECTION D (15 Marks)
Question 8
(a) With the help of a labeled ray diagram, explain the working of an astronomical telescope in normal adjustment. Derive the expression for its magnifying power. [5]
OR
(b) State the postulates of Bohr's atomic model. Derive an expression for the radius of the nth orbit of an electron in a hydrogen atom. [5]
"""

# 2. Mathematics Benchmark Document Text (CISCE Pattern)
MATHS_2026_TEXT = """%PDF-1.4 Benchmark Simulated Document
COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS
ISC CLASS XII SPECIMEN QUESTION PAPER 2026
MATHEMATICS
Maximum Marks: 80
Time Allowed: Three hours

SECTION A (65 Marks)
Question 1
If A is a square matrix of order 3 such that det(A) = 5, then find the value of det(3A). [2]

Question 2
Evaluate the following definite integral: integral from 0 to pi/2 of (sin x) / (sin x + cos x) dx. [4]

Question 3
Find the general solution of the differential equation: (x^2 + 1) dy/dx + 2xy = 4x^2. [4]

Question 4
A card from a pack of 52 playing cards is lost. From the remaining cards, two cards are drawn and are found to be both diamonds. Find the probability that the lost card was a diamond. [6]

SECTION B (15 Marks)
Question 5
Find the shortest distance between the two skew lines whose vector equations are r = (i + 2j + 3k) + lambda(i - 3j + 2k) and r = (4i + 5j + 6k) + mu(2i + 3j + k). [6]
"""

def generate_benchmarks():
    # Targets corresponding exactly to Step 5 registry
    phys_path = os.path.join(
        BASE_DIR, "02_specimen_papers", "861_physics", "ISC_Specimen_Paper_Physics_861.pdf"
    )
    math_path = os.path.join(
        BASE_DIR, "02_specimen_papers", "860_mathematics", "ISC_Specimen_Paper_Mathematics_860.pdf"
    )

    os.makedirs(os.path.dirname(phys_path), exist_ok=True)
    os.makedirs(os.path.dirname(math_path), exist_ok=True)

    with open(phys_path, "w", encoding="utf-8") as f:
        f.write(PHYSICS_2026_TEXT)
    print(f"[CREATED] Physics benchmark paper written to: {phys_path}")

    with open(math_path, "w", encoding="utf-8") as f:
        f.write(MATHS_2026_TEXT)
    print(f"[CREATED] Mathematics benchmark paper written to: {math_path}")

if __name__ == "__main__":
    generate_benchmarks()