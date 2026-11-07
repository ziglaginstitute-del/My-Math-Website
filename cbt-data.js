/* 
  =========================================
  ZIGLAG INSTITUTE CBT EXAMINATION QUESTION BANK
  Authentic Past Questions for JAMB UTME & WASSCE/NECO
  =========================================
*/

const CBT_SUBJECTS = [
  { id: 'mathematics', name: 'General Mathematics', icon: '📐', count: 10, defaultTime: 30 },
  { id: 'physics', name: 'Physics', icon: '⚡', count: 10, defaultTime: 30 },
  { id: 'english', name: 'Use of English', icon: '📖', count: 10, defaultTime: 25 },
  { id: 'chemistry', name: 'Chemistry', icon: '🧪', count: 8, defaultTime: 25 },
  { id: 'biology', name: 'Biology', icon: '🧬', count: 8, defaultTime: 25 }
];

const CBT_QUESTION_BANK = {
  mathematics: [
    {
      id: 'm-1',
      subject: 'mathematics',
      topic: 'Linear Equations & Algebra',
      difficulty: 'Beginner',
      question: 'Solve for x in the linear equation: 3(x - 2) + 4 = 2(x + 5)',
      options: [
        { label: 'A', text: 'x = 8' },
        { label: 'B', text: 'x = 12' },
        { label: 'C', text: 'x = 14' },
        { label: 'D', text: 'x = 10' }
      ],
      correct: 'B',
      explanation: 'Expanding brackets: 3x - 6 + 4 = 2x + 10 ⟹ 3x - 2 = 2x + 10. Subtracting 2x from both sides gives x - 2 = 10. Adding 2 yields x = 12.'
    },
    {
      id: 'm-2',
      subject: 'mathematics',
      topic: 'Logarithms & Indices',
      difficulty: 'Intermediate',
      question: 'If log₁₀(2) = 0.3010 and log₁₀(3) = 0.4771, calculate the exact value of log₁₀(18).',
      options: [
        { label: 'A', text: '1.2552' },
        { label: 'B', text: '0.9542' },
        { label: 'C', text: '1.1761' },
        { label: 'D', text: '1.0791' }
      ],
      correct: 'A',
      explanation: 'Factor 18 into prime factors: 18 = 2 × 3² = 2 × 9. Applying logarithmic expansion laws: log₁₀(18) = log₁₀(2) + 2·log₁₀(3) = 0.3010 + 2(0.4771) = 0.3010 + 0.9542 = 1.2552.'
    },
    {
      id: 'm-3',
      subject: 'mathematics',
      topic: 'Differential Calculus',
      difficulty: 'Intermediate',
      question: 'Find the derivative dy/dx of the polynomial function: y = 4x³ - 5x² + 7x - 9',
      options: [
        { label: 'A', text: '12x² - 10x + 7' },
        { label: 'B', text: '12x³ - 10x² + 7' },
        { label: 'C', text: '4x² - 5x + 7' },
        { label: 'D', text: '12x² - 5x' }
      ],
      correct: 'A',
      explanation: 'Apply the power rule d/dx[axⁿ] = n·axⁿ⁻¹. Differentiating each term: d/dx(4x³) = 12x², d/dx(-5x²) = -10x, d/dx(7x) = 7, and d/dx(-9) = 0. Summing gives dy/dx = 12x² - 10x + 7.'
    },
    {
      id: 'm-4',
      subject: 'mathematics',
      topic: 'Probability & Permutations',
      difficulty: 'Advanced',
      question: 'A fair die is rolled twice. What is the probability that the sum of the numbers obtained is at least 10?',
      options: [
        { label: 'A', text: '1/6' },
        { label: 'B', text: '1/12' },
        { label: 'C', text: '5/36' },
        { label: 'D', text: '7/36' }
      ],
      correct: 'A',
      explanation: 'Total sample space outcomes = 6 × 6 = 36. Favorable outcomes where sum ≥ 10:\nSum = 10: (4,6), (5,5), (6,4) [3 pairs]\nSum = 11: (5,6), (6,5) [2 pairs]\nSum = 12: (6,6) [1 pair]\nTotal favorable = 3 + 2 + 1 = 6. Probability = 6/36 = 1/6.'
    },
    {
      id: 'm-5',
      subject: 'mathematics',
      topic: 'Sequences & Series (G.P.)',
      difficulty: 'Intermediate',
      question: 'The third term (T₃) of a Geometric Progression (G.P.) is 12 and the sixth term (T₆) is 96. What is the first term (a)?',
      options: [
        { label: 'A', text: '2' },
        { label: 'B', text: '3' },
        { label: 'C', text: '4' },
        { label: 'D', text: '6' }
      ],
      correct: 'B',
      explanation: 'General term of a G.P. is Tₙ = a·rⁿ⁻¹. Here T₃ = a·r² = 12 and T₆ = a·r⁵ = 96. Dividing T₆ by T₃: (a·r⁵)/(a·r²) = r³ = 96/12 = 8 ⟹ r = 2. Substituting r into T₃: a(2)² = 12 ⟹ 4a = 12 ⟹ a = 3.'
    },
    {
      id: 'm-6',
      subject: 'mathematics',
      topic: 'Modular Arithmetic & Number Bases',
      difficulty: 'Intermediate',
      question: 'Solve for x in the modular congruence equation: 3x ≡ 4 (mod 5), where 0 ≤ x < 5.',
      options: [
        { label: 'A', text: 'x = 1' },
        { label: 'B', text: 'x = 3' },
        { label: 'C', text: 'x = 2' },
        { label: 'D', text: 'x = 4' }
      ],
      correct: 'B',
      explanation: 'Testing integer values for x between 0 and 4: For x = 3: 3(3) = 9. 9 divided by 5 yields a quotient of 1 with remainder 4. Therefore 9 ≡ 4 (mod 5), making x = 3 the exact solution.'
    },
    {
      id: 'm-7',
      subject: 'mathematics',
      topic: 'Matrices & Determinants',
      difficulty: 'Intermediate',
      question: 'Evaluate the determinant of the 2×2 matrix M = [[5, -2], [3, 4]].',
      options: [
        { label: 'A', text: '14' },
        { label: 'B', text: '26' },
        { label: 'C', text: '20' },
        { label: 'D', text: '17' }
      ],
      correct: 'B',
      explanation: 'For any 2×2 matrix [[a, b], [c, d]], det(M) = ad - bc. Substituting values: det(M) = (5)(4) - (-2)(3) = 20 - (-6) = 20 + 6 = 26.'
    },
    {
      id: 'm-8',
      subject: 'mathematics',
      topic: 'Quadratic Equations',
      difficulty: 'Beginner',
      question: 'Find the roots of the quadratic equation: 2x² - 7x + 3 = 0',
      options: [
        { label: 'A', text: 'x = 3 or x = 1/2' },
        { label: 'B', text: 'x = -3 or x = -1/2' },
        { label: 'C', text: 'x = 2 or x = 3/2' },
        { label: 'D', text: 'x = 1 or x = 6' }
      ],
      correct: 'A',
      explanation: 'Using factorization: Multiply a·c = 2 × 3 = 6. Two factors of 6 that sum to -7 are -6 and -1. Rewrite: 2x² - 6x - x + 3 = 0 ⟹ 2x(x - 3) - 1(x - 3) = 0 ⟹ (2x - 1)(x - 3) = 0. Roots are x = 1/2 or x = 3.'
    },
    {
      id: 'm-9',
      subject: 'mathematics',
      topic: 'Definite Integration',
      difficulty: 'Advanced',
      question: 'Evaluate the definite integral: ∫₁³ (3x² - 2x + 1) dx',
      options: [
        { label: 'A', text: '18' },
        { label: 'B', text: '20' },
        { label: 'C', text: '22' },
        { label: 'D', text: '24' }
      ],
      correct: 'B',
      explanation: 'Integrating term by term: ∫(3x² - 2x + 1)dx = [x³ - x² + x] from 1 to 3. Upper limit (x = 3): (27 - 9 + 3) = 21. Lower limit (x = 1): (1 - 1 + 1) = 1. Result = 21 - 1 = 20.'
    },
    {
      id: 'm-10',
      subject: 'mathematics',
      topic: 'Coordinate Geometry',
      difficulty: 'Intermediate',
      question: 'What is the gradient (slope) of the straight line perpendicular to the line 3x - 6y + 8 = 0?',
      options: [
        { label: 'A', text: '1/2' },
        { label: 'B', text: '-2' },
        { label: 'C', text: '2' },
        { label: 'D', text: '-1/2' }
      ],
      correct: 'B',
      explanation: 'Express the given line in slope-intercept form y = mx + c: -6y = -3x - 8 ⟹ y = (1/2)x + 4/3. The slope m₁ = 1/2. Perpendicular lines satisfy m₁ · m₂ = -1 ⟹ (1/2)m₂ = -1 ⟹ m₂ = -2.'
    }
  ],

  physics: [
    {
      id: 'p-1',
      subject: 'physics',
      topic: 'Kinematics & Motion',
      difficulty: 'Beginner',
      question: 'A car accelerates uniformly from rest to a velocity of 20 m/s in 5 seconds. What is the acceleration of the car?',
      options: [
        { label: 'A', text: '2 m/s²' },
        { label: 'B', text: '4 m/s²' },
        { label: 'C', text: '5 m/s²' },
        { label: 'D', text: '100 m/s²' }
      ],
      correct: 'B',
      explanation: 'Using the first equation of linear motion: v = u + at. Here initial velocity u = 0 m/s, final velocity v = 20 m/s, and time t = 5 s. Therefore a = (v - u)/t = (20 - 0)/5 = 4 m/s².'
    },
    {
      id: 'p-2',
      subject: 'physics',
      topic: 'Current Electricity & Power',
      difficulty: 'Intermediate',
      question: 'An electric kettle rated 2.0 kW is connected across a 240 V mains supply. What is the electric current drawn by the kettle?',
      options: [
        { label: 'A', text: '8.33 A' },
        { label: 'B', text: '12.0 A' },
        { label: 'C', text: '0.12 A' },
        { label: 'D', text: '480 A' }
      ],
      correct: 'A',
      explanation: 'Electric power P = V × I. Convert 2.0 kW to Watts: P = 2.0 × 1000 = 2000 W. Rearranging for current: I = P / V = 2000 / 240 = 8.33 A.'
    },
    {
      id: 'p-3',
      subject: 'physics',
      topic: 'Radioactivity & Nuclear Physics',
      difficulty: 'Advanced',
      question: 'A radioactive isotope has a half-life of 8 days. If an initial mass of 80 g is stored, what mass remains undecayed after 32 days?',
      options: [
        { label: 'A', text: '10 g' },
        { label: 'B', text: '5 g' },
        { label: 'C', text: '2.5 g' },
        { label: 'D', text: '1.25 g' }
      ],
      correct: 'B',
      explanation: 'Number of elapsed half-lives n = total time / half-life period = 32 / 8 = 4 half-lives. Remaining mass N = N₀ / 2ⁿ = 80 / (2⁴) = 80 / 16 = 5 g.'
    },
    {
      id: 'p-4',
      subject: 'physics',
      topic: 'Optics & Lenses',
      difficulty: 'Intermediate',
      question: 'Which of the following optical conditions produces an upright, magnified, and virtual image in a converging lens?',
      options: [
        { label: 'A', text: 'Object placed within the focal length (u < f)' },
        { label: 'B', text: 'Object placed at twice the focal length (u = 2f)' },
        { label: 'C', text: 'Object placed at infinity' },
        { label: 'D', text: 'Object placed between f and 2f' }
      ],
      correct: 'A',
      explanation: 'When an object is placed inside the focal length (u < f) of a convex (converging) lens (as in a magnifying glass), the refracted rays diverge and their backward extrapolations form an erect, magnified, virtual image on the same side.'
    },
    {
      id: 'p-5',
      subject: 'physics',
      topic: 'Waves & Sound',
      difficulty: 'Beginner',
      question: 'A sound wave of frequency 500 Hz travels through air at a speed of 340 m/s. What is its wavelength?',
      options: [
        { label: 'A', text: '0.68 m' },
        { label: 'B', text: '1.47 m' },
        { label: 'C', text: '170 m' },
        { label: 'D', text: '0.34 m' }
      ],
      correct: 'A',
      explanation: 'Using the wave relation v = f · λ, where v is velocity, f is frequency, and λ is wavelength. Therefore λ = v / f = 340 / 500 = 0.68 m.'
    },
    {
      id: 'p-6',
      subject: 'physics',
      topic: 'Work, Energy & Power',
      difficulty: 'Beginner',
      question: 'A force of 50 N acts on a body of mass 10 kg, displacing it through 6 m in the direction of the force. What is the work done?',
      options: [
        { label: 'A', text: '300 J' },
        { label: 'B', text: '500 J' },
        { label: 'C', text: '60 J' },
        { label: 'D', text: '3000 J' }
      ],
      correct: 'A',
      explanation: 'Work done W = Force × Displacement = F × d = 50 N × 6 m = 300 Joules.'
    },
    {
      id: 'p-7',
      subject: 'physics',
      topic: 'Thermal Expansion & Heat',
      difficulty: 'Intermediate',
      question: 'Calculate the heat energy required to raise the temperature of 2 kg of water from 20°C to 70°C. (Specific heat capacity of water c = 4200 J/kg°C)',
      options: [
        { label: 'A', text: '420,000 J' },
        { label: 'B', text: '210,000 J' },
        { label: 'C', text: '105,000 J' },
        { label: 'D', text: '84,000 J' }
      ],
      correct: 'A',
      explanation: 'Heat energy Q = m · c · Δθ. Here mass m = 2 kg, specific heat c = 4200 J/kg°C, and temperature change Δθ = 70 - 20 = 50°C. Therefore Q = 2 × 4200 × 50 = 420,000 J.'
    },
    {
      id: 'p-8',
      subject: 'physics',
      topic: 'Gas Laws & Thermodynamics',
      difficulty: 'Intermediate',
      question: 'According to Boyle\'s Law, the pressure of a fixed mass of gas at constant temperature is:',
      options: [
        { label: 'A', text: 'Inversely proportional to its volume' },
        { label: 'B', text: 'Directly proportional to its volume' },
        { label: 'C', text: 'Inversely proportional to its absolute temperature' },
        { label: 'D', text: 'Equal to its density' }
      ],
      correct: 'A',
      explanation: 'Boyle\'s Law states that at constant temperature, the pressure P of a given mass of an ideal gas is inversely proportional to its volume V (P ∝ 1/V ⟹ PV = constant).'
    },
    {
      id: 'p-9',
      subject: 'physics',
      topic: 'Electrostatics',
      difficulty: 'Intermediate',
      question: 'Two point charges of +2 μC and +4 μC are separated by a distance r. If the distance between them is doubled, the electrostatic force between them becomes:',
      options: [
        { label: 'A', text: 'One-fourth of the initial force' },
        { label: 'B', text: 'Half of the initial force' },
        { label: 'C', text: 'Double the initial force' },
        { label: 'D', text: 'Four times the initial force' }
      ],
      correct: 'A',
      explanation: 'By Coulomb\'s inverse square law: F ∝ 1/r². When distance is doubled (r\' = 2r), F\' ∝ 1/(2r)² = 1/(4r²) = (1/4)F. The force reduces to one-fourth.'
    },
    {
      id: 'p-10',
      subject: 'physics',
      topic: 'Simple Harmonic Motion',
      difficulty: 'Advanced',
      question: 'A simple pendulum has a period of 2.0 seconds on Earth. If its length is multiplied by 4, what will be its new period of oscillation?',
      options: [
        { label: 'A', text: '4.0 s' },
        { label: 'B', text: '8.0 s' },
        { label: 'C', text: '1.0 s' },
        { label: 'D', text: '0.5 s' }
      ],
      correct: 'A',
      explanation: 'The period of a simple pendulum is T = 2π√(L/g), meaning T ∝ √L. If length is multiplied by 4 (L\' = 4L), the new period T\' = 2π√(4L/g) = 2 · [2π√(L/g)] = 2 × 2.0 s = 4.0 seconds.'
    }
  ],

  english: [
    {
      id: 'e-1',
      subject: 'english',
      topic: 'Synonyms (Nearest in Meaning)',
      difficulty: 'Beginner',
      question: 'Choose the word nearest in meaning to the capitalized word: The principal gave a LUCID explanation of the new school regulations.',
      options: [
        { label: 'A', text: 'Vague and complicated' },
        { label: 'B', text: 'Clear and easily understood' },
        { label: 'C', text: 'Lengthy and tedious' },
        { label: 'D', text: 'Ambiguous and controversial' }
      ],
      correct: 'B',
      explanation: '“Lucid” derives from the Latin root lux (light). A lucid explanation is transparent, coherent, and simple to comprehend.'
    },
    {
      id: 'e-2',
      subject: 'english',
      topic: 'Concord & Syntax',
      difficulty: 'Intermediate',
      question: 'Complete the sentence with the most appropriate option: Neither the teacher nor the students _______ present at the national symposium.',
      options: [
        { label: 'A', text: 'was' },
        { label: 'B', text: 'were' },
        { label: 'C', text: 'is' },
        { label: 'D', text: 'are being' }
      ],
      correct: 'B',
      explanation: 'Under the rule of proximity with correlative conjunctions (neither...nor), the verb agrees with the subject closest to it. "The students" is plural and adjacent to the blank, requiring the plural past verb "were".'
    },
    {
      id: 'e-3',
      subject: 'english',
      topic: 'Idiomatic Expressions',
      difficulty: 'Intermediate',
      question: 'Choose the option that best interprets the idiom: The manager decided to "bite the bullet" and announce the budget cuts.',
      options: [
        { label: 'A', text: 'To act violently during a board meeting' },
        { label: 'B', text: 'To face a tough, unpleasant situation with courage' },
        { label: 'C', text: 'To indefinitely postpone a decision' },
        { label: 'D', text: 'To delegate responsibility to junior assistants' }
      ],
      correct: 'B',
      explanation: '“To bite the bullet” is an English idiom meaning to accept an inevitable, painful, or challenging ordeal with fortitude.'
    },
    {
      id: 'e-4',
      subject: 'english',
      topic: 'Antonyms (Opposite in Meaning)',
      difficulty: 'Advanced',
      question: 'Identify the word opposite in meaning to the capitalized word: The senator was widely criticized for his BELLICOSE rhetoric.',
      options: [
        { label: 'A', text: 'Aggressive' },
        { label: 'B', text: 'Pugnacious' },
        { label: 'C', text: 'Pacifistic' },
        { label: 'D', text: 'Hostile' }
      ],
      correct: 'C',
      explanation: 'Bellicose means demonstrating aggression and eagerness to fight (from Latin bellum = war). The exact opposite is peaceful or pacifistic.'
    },
    {
      id: 'e-5',
      subject: 'english',
      topic: 'Phonetics & Vowel Sounds',
      difficulty: 'Intermediate',
      question: 'From the options lettered A to D, choose the word that has the same vowel sound as in: "b-i-r-d" (/ɜː/)',
      options: [
        { label: 'A', text: 'Bread' },
        { label: 'B', text: 'Word' },
        { label: 'C', text: 'Board' },
        { label: 'D', text: 'Bead' }
      ],
      correct: 'B',
      explanation: '“Bird” is pronounced /bɜːd/. “Word” is pronounced /wɜːd/, which contains the identical central long vowel sound /ɜː/.'
    },
    {
      id: 'e-6',
      subject: 'english',
      topic: 'Prepositions & Tenses',
      difficulty: 'Beginner',
      question: 'Select the option that best completes the sentence: She has lived in Lagos _______ five years.',
      options: [
        { label: 'A', text: 'since' },
        { label: 'B', text: 'for' },
        { label: 'C', text: 'during' },
        { label: 'D', text: 'from' }
      ],
      correct: 'B',
      explanation: 'Use the preposition "for" with periods of duration (e.g. for five years), whereas "since" denotes a specific starting point in time (e.g. since 2021).'
    },
    {
      id: 'e-7',
      subject: 'english',
      topic: 'Spelling & Vocabulary',
      difficulty: 'Intermediate',
      question: 'Which of the following words is correctly spelt?',
      options: [
        { label: 'A', text: 'Accomodation' },
        { label: 'B', text: 'Accommodation' },
        { label: 'C', text: 'Acommodation' },
        { label: 'D', text: 'Acomodation' }
      ],
      correct: 'B',
      explanation: 'The word "Accommodation" contains double \'c\' and double \'m\' (A-c-c-o-m-m-o-d-a-t-i-o-n).'
    },
    {
      id: 'e-8',
      subject: 'english',
      topic: 'Sentence Completion',
      difficulty: 'Intermediate',
      question: 'The criminal was convicted _______ armed robbery and sentenced to ten years.',
      options: [
        { label: 'A', text: 'for' },
        { label: 'B', text: 'of' },
        { label: 'C', text: 'with' },
        { label: 'D', text: 'about' }
      ],
      correct: 'B',
      explanation: 'The standard preposition following the verb "convict" when referring to a crime is "of" (convicted of a crime).'
    },
    {
      id: 'e-9',
      subject: 'english',
      topic: 'Question Tags',
      difficulty: 'Beginner',
      question: 'You haven\'t finished your exam practice yet, _______?',
      options: [
        { label: 'A', text: 'haven\'t you' },
        { label: 'B', text: 'have you' },
        { label: 'C', text: 'did you' },
        { label: 'D', text: 'is it' }
      ],
      correct: 'B',
      explanation: 'A negative statement takes a positive tag: "haven\'t finished" requires the positive tag "have you?".'
    },
    {
      id: 'e-10',
      subject: 'english',
      topic: 'Direct & Reported Speech',
      difficulty: 'Intermediate',
      question: 'Choose the correct indirect form: He said, "I will write the JAMB exam next week."',
      options: [
        { label: 'A', text: 'He said that he will write the JAMB exam next week.' },
        { label: 'B', text: 'He said that he would write the JAMB exam the following week.' },
        { label: 'C', text: 'He said that he wrote the JAMB exam next week.' },
        { label: 'D', text: 'He said he is writing the JAMB exam the following week.' }
      ],
      correct: 'B',
      explanation: 'In indirect speech, "will" shifts to the conditional "would", and temporal expression "next week" shifts to "the following week".'
    }
  ],

  chemistry: [
    {
      id: 'c-1',
      subject: 'chemistry',
      topic: 'Periodic Table & Atomic Structure',
      difficulty: 'Beginner',
      question: 'What is the electronic configuration of an element with atomic number 17 (Chlorine)?',
      options: [
        { label: 'A', text: '1s² 2s² 2p⁶ 3s² 3p⁵' },
        { label: 'B', text: '1s² 2s² 2p⁶ 3s² 3p⁶' },
        { label: 'C', text: '1s² 2s² 2p⁶ 3s¹ 3p⁶' },
        { label: 'D', text: '1s² 2s² 2p⁶ 3s² 3p⁴' }
      ],
      correct: 'A',
      explanation: 'Chlorine has 17 electrons. Following the Aufbau principle: 1s² (2) + 2s² 2p⁶ (8) + 3s² 3p⁵ (7) = 17 electrons.'
    },
    {
      id: 'c-2',
      subject: 'chemistry',
      topic: 'Mole Concept & Stoichiometry',
      difficulty: 'Intermediate',
      question: 'Calculate the mass of 0.5 moles of Calcium Carbonate (CaCO₃). (Atomic masses: Ca = 40, C = 12, O = 16)',
      options: [
        { label: 'A', text: '100 g' },
        { label: 'B', text: '50 g' },
        { label: 'C', text: '25 g' },
        { label: 'D', text: '75 g' }
      ],
      correct: 'B',
      explanation: 'Molar mass of CaCO₃ = 40 + 12 + 3(16) = 40 + 12 + 48 = 100 g/mol. Mass = Moles × Molar Mass = 0.5 mol × 100 g/mol = 50 g.'
    },
    {
      id: 'c-3',
      subject: 'chemistry',
      topic: 'Acids, Bases & Salts',
      difficulty: 'Beginner',
      question: 'What is the pH of a 0.01 mol/dm³ solution of hydrochloric acid (HCl), assuming complete dissociation?',
      options: [
        { label: 'A', text: '1.0' },
        { label: 'B', text: '2.0' },
        { label: 'C', text: '3.0' },
        { label: 'D', text: '7.0' }
      ],
      correct: 'B',
      explanation: 'HCl is a strong monoprotic acid, so [H⁺] = 0.01 = 10⁻² mol/dm³. pH = -log₁₀[H⁺] = -log₁₀(10⁻²) = 2.0.'
    },
    {
      id: 'c-4',
      subject: 'chemistry',
      topic: 'Organic Chemistry (Hydrocarbons)',
      difficulty: 'Intermediate',
      question: 'Which of the following organic compounds decolourizes bromine water in tetrachloromethane in the dark?',
      options: [
        { label: 'A', text: 'Ethane' },
        { label: 'B', text: 'Ethene' },
        { label: 'C', text: 'Methane' },
        { label: 'D', text: 'Propane' }
      ],
      correct: 'B',
      explanation: 'Ethene is an unsaturated alkene containing a carbon-carbon double bond (C=C). It rapidly undergoes electrophilic addition across the double bond to decolorize reddish-brown bromine water to colorless 1,2-dibromoethane.'
    },
    {
      id: 'c-5',
      subject: 'chemistry',
      topic: 'Electrochemistry',
      difficulty: 'Advanced',
      question: 'During the electrolysis of acidified water using inert platinum electrodes, what substance is discharged at the cathode?',
      options: [
        { label: 'A', text: 'Oxygen gas' },
        { label: 'B', text: 'Hydrogen gas' },
        { label: 'C', text: 'Chlorine gas' },
        { label: 'D', text: 'Platinum deposit' }
      ],
      correct: 'B',
      explanation: 'At the cathode (reduction electrode), hydrogen ions (H⁺) are reduced by gaining electrons to evolve Hydrogen gas: 2H⁺ + 2e⁻ ⟶ H₂(g). Oxygen is discharged at the anode.'
    },
    {
      id: 'c-6',
      subject: 'chemistry',
      topic: 'Gas Volumes (Avogadro\'s Law)',
      difficulty: 'Intermediate',
      question: 'What volume does 0.25 moles of any ideal gas occupy at standard temperature and pressure (s.t.p.)? (Molar volume at s.t.p. = 22.4 dm³)',
      options: [
        { label: 'A', text: '5.6 dm³' },
        { label: 'B', text: '11.2 dm³' },
        { label: 'C', text: '22.4 dm³' },
        { label: 'D', text: '44.8 dm³' }
      ],
      correct: 'A',
      explanation: 'Volume = Moles × Molar volume at s.t.p. = 0.25 × 22.4 dm³ = 5.6 dm³.'
    },
    {
      id: 'c-7',
      subject: 'chemistry',
      topic: 'Chemical Bonding',
      difficulty: 'Beginner',
      question: 'Which of the following substances possesses a giant covalent lattice structure?',
      options: [
        { label: 'A', text: 'Diamond' },
        { label: 'B', text: 'Sodium Chloride' },
        { label: 'C', text: 'Water' },
        { label: 'D', text: 'Carbon dioxide' }
      ],
      correct: 'A',
      explanation: 'Diamond is an allotrope of carbon where each carbon atom is tetrahedrally bonded to four other carbons via strong covalent bonds in a continuous 3D giant macromolecular lattice.'
    },
    {
      id: 'c-8',
      subject: 'chemistry',
      topic: 'Redox Reactions',
      difficulty: 'Intermediate',
      question: 'In the reaction: CuO + H₂ ⟶ Cu + H₂O, which substance undergoes oxidation?',
      options: [
        { label: 'A', text: 'CuO' },
        { label: 'B', text: 'H₂' },
        { label: 'C', text: 'Cu' },
        { label: 'D', text: 'H₂O' }
      ],
      correct: 'B',
      explanation: 'Oxidation is the gain of oxygen or loss of electrons. Hydrogen (H₂) gains oxygen to form H₂O, so H₂ is the substance oxidized. CuO loses oxygen and is reduced.'
    }
  ],

  biology: [
    {
      id: 'b-1',
      subject: 'biology',
      topic: 'Cell Biology & Organelles',
      difficulty: 'Beginner',
      question: 'Which organelle is universally referred to as the powerhouse of the eukaryotic cell?',
      options: [
        { label: 'A', text: 'Ribosome' },
        { label: 'B', text: 'Mitochondrion' },
        { label: 'C', text: 'Golgi apparatus' },
        { label: 'D', text: 'Endoplasmic reticulum' }
      ],
      correct: 'B',
      explanation: 'Mitochondria generate the majority of cellular chemical energy in the form of Adenosine Triphosphate (ATP) via aerobic cellular respiration.'
    },
    {
      id: 'b-2',
      subject: 'biology',
      topic: 'Genetics & Heredity',
      difficulty: 'Intermediate',
      question: 'In humans, if two heterozygous parents for sickle cell anemia (HbA HbS) have children, what is the probability of a child having full sickle cell disease (HbS HbS)?',
      options: [
        { label: 'A', text: '25% (1 in 4)' },
        { label: 'B', text: '50% (2 in 4)' },
        { label: 'C', text: '75% (3 in 4)' },
        { label: 'D', text: '0%' }
      ],
      correct: 'A',
      explanation: 'Crossing AS × AS yields offspring genotypes: 1 AA (25%), 2 AS (50%), and 1 SS (25%). Therefore the probability of an SS child is 1/4 or 25%.'
    },
    {
      id: 'b-3',
      subject: 'biology',
      topic: 'Ecology & Feeding Relationships',
      difficulty: 'Beginner',
      question: 'In any stable terrestrial ecosystem, the primary producers in the food chain are:',
      options: [
        { label: 'A', text: 'Herbivores' },
        { label: 'B', text: 'Green photosynthetic plants' },
        { label: 'C', text: 'Carnivores' },
        { label: 'D', text: 'Decomposers' }
      ],
      correct: 'B',
      explanation: 'Green plants (autotrophs) synthesize organic matter directly from sunlight, water, and carbon dioxide through photosynthesis, forming the foundational trophic level.'
    },
    {
      id: 'b-4',
      subject: 'biology',
      topic: 'Circulatory System',
      difficulty: 'Intermediate',
      question: 'Which blood vessel conveys oxygenated blood directly from the lungs to the left atrium of the human heart?',
      options: [
        { label: 'A', text: 'Pulmonary artery' },
        { label: 'B', text: 'Pulmonary vein' },
        { label: 'C', text: 'Aorta' },
        { label: 'D', text: 'Vena cava' }
      ],
      correct: 'B',
      explanation: 'The pulmonary vein is unique among veins as it carries freshly oxygenated blood from the lungs back to the left atrium of the heart.'
    },
    {
      id: 'b-5',
      subject: 'biology',
      topic: 'Plant Physiology',
      difficulty: 'Intermediate',
      question: 'The vascular tissue responsible for transporting dissolved sugars and organic nutrients from leaves to other parts of a plant is:',
      options: [
        { label: 'A', text: 'Xylem' },
        { label: 'B', text: 'Phloem' },
        { label: 'C', text: 'Cambium' },
        { label: 'D', text: 'Pith' }
      ],
      correct: 'B',
      explanation: 'Phloem tissue conducts synthesized sucrose and amino acids bidirectionally (translocation). Xylem conducts water and mineral salts upward from roots.'
    },
    {
      id: 'b-6',
      subject: 'biology',
      topic: 'Human Excretion',
      difficulty: 'Intermediate',
      question: 'What is the structural and functional microscopic filtration unit of the human kidney?',
      options: [
        { label: 'A', text: 'Neuron' },
        { label: 'B', text: 'Nephron' },
        { label: 'C', text: 'Alveolus' },
        { label: 'D', text: 'Villus' }
      ],
      correct: 'B',
      explanation: 'The nephron is the basic functional unit of the kidney responsible for ultrafiltration, selective reabsorption, and urine production.'
    },
    {
      id: 'b-7',
      subject: 'biology',
      topic: 'Enzymes & Digestion',
      difficulty: 'Beginner',
      question: 'The enzyme salivary amylase (ptyalin) initiates the chemical digestion of which nutrient in the human mouth?',
      options: [
        { label: 'A', text: 'Proteins' },
        { label: 'B', text: 'Fats and lipids' },
        { label: 'C', text: 'Starch (cooked carbohydrates)' },
        { label: 'D', text: 'Nucleic acids' }
      ],
      correct: 'C',
      explanation: 'Salivary amylase breaks down complex starch polysaccharides into simpler disaccharides such as maltose in the oral cavity.'
    },
    {
      id: 'b-8',
      subject: 'biology',
      topic: 'Homeostasis & Hormones',
      difficulty: 'Intermediate',
      question: 'Which endocrine hormone secreted by the islets of Langerhans in the pancreas decreases blood glucose concentration?',
      options: [
        { label: 'A', text: 'Glucagon' },
        { label: 'B', text: 'Insulin' },
        { label: 'C', text: 'Adrenaline' },
        { label: 'D', text: 'Thyroxine' }
      ],
      correct: 'B',
      explanation: 'Insulin promotes the cellular uptake of glucose and stimulates glycogen synthesis in the liver and muscles, lowering elevated blood sugar levels.'
    }
  ]
};
