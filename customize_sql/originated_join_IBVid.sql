USE LF_LMSMASTER
DROP TABLE IF EXISTS #t1;
SELECT
    A.Application_ID, A.ApplicationSteps, A.LPCampaign, D.DenialCode, D.DenialDescription,A.PortfolioID, A.CustomerID, A.CustomerSSN, A.ApplicationDate, A.Score, CustEmail,
    CASE WHEN ApplicationSteps LIKE '%S%' THEN 1 ELSE 0 END AS NewlyScored,
    CASE WHEN A.ApplicationStatus IN ('A','P') THEN 1 ELSE 0 END AS Accepted,
    CASE WHEN A.ApplicationStatus IN ('A','P') THEN A.LeadPurchasePrice ELSE 0 END AS LeadPurchasePrice,
    CASE WHEN L.LoanStatus NOT IN ('V','W','G','K') AND A.ApplicationStatus='J' THEN 1 ELSE 0 END AS PartialPreApproved,
    CASE WHEN L.LoanStatus NOT IN ('V','W','G','K') THEN 1 ELSE 0 END AS Originated,
    L.LoanID,
    DATEDIFF(YEAR, VW.DOB, A.ApplicationDate) AS Age,
    CASE WHEN VW.Frequency IN ('B','S') THEN 'B' ELSE VW.Frequency END AS Frequency,
    CASE WHEN L.LoanStatus NOT IN ('V','W','G','K') THEN L.OriginatedAmount ELSE NULL END AS OriginatedAmount,
    OriginationDate,
    LoanStatus,
    CASE WHEN ((L.RenewalLoanId <> '0') OR (A.LPCampaign = 'RENEW')) THEN 'RENEWAL'
         WHEN ApplicationSteps NOT LIKE '%R%' THEN 'NEW'
         ELSE 'REPEAT' END AS CustType,
    RenewalLoanId
INTO #t1
FROM Application A
LEFT JOIN Loans L
  ON A.Application_ID = L.ApplicationID AND A.PortFolioID = L.PortFolioID
LEFT JOIN LF_LMS_Logs..VW_ApplicationDump VW
  ON A.APPGUID = VW.APPGUID
LEFT JOIN LF_LMSMASTER..DenialCode D
  ON A.DenialCode = D.DenialCode

where ((VW.CustEmail is null) or  (VW.CustEmail not in ( 'josh@concordadvice.com', 'tiffany.speedyservicing@gmail.com','bobby@speedyservicing.com',
'and.kom@example.com', 'and.tor020@example.com', 'and.tor050@example.com', 'and.torrc4@example.com',
'test@dot818.com', 'test@example.com', 'test@gmail.com', 'test@loanscanada.ca', 'test@test.com', 'test2@test.com',
'testerqad@gmail.com', 'testik@test.com', 'testteam@dmaassociatescorp.com', 'tiffany.speedyservicing@gmail.com')))


UPDATE #t1 -- update the renewal loanid from 0 to correct previous loanIDs
SET #t1.RenewalLoanId = B.RenewalLoanId
from #t1 A inner join (select * from
(select A.LoanID, L.LoanID as RenewalLoanId, row_number() over (partition by A.LoanID order by datediff(day, L.OriginationDate, A.OriginationDate) desc) as RN from #t1 A
inner join Application A2 on A.CustomerID = A2.CustomerID and A2.ApplicationDate < A.ApplicationDate
inner join Loans L on A2.Application_ID = L.ApplicationID and A2.PortFolioID = L.PortFolioID and L.OriginationDate < A.OriginationDate and L.LoanStatus not in ('W','V','G','K')
where A.CustType = 'RENEWAL' and A.RenewalLoanId = '0') K where RN=1) B on A.LoanID = B.LoanID

------------ narrow to only originated ------------------
DROP TABLE IF EXISTS #t2;

SELECT
    *
INTO #t2
FROM #t1
WHERE Originated = 1;   -- 20412 originated all time on 01/20/2026

SELECT TOP 10 *
FROM #t2


 -----------  FPDAA Loonie Logic ------------------------------
DROP TABLE IF EXISTS #fpdaa_t;

SELECT
    Application_ID,
    PortfolioID,
    LoanID,
    1 - MAX(FstInstPaidOff) AS FPDAA
INTO #fpdaa_t
FROM (
    SELECT
        A.Application_ID,
        A.PortfolioID,
        A.LoanID,
        CASE WHEN P.PaymentStatus = 'D' THEN 1 ELSE 0 END AS FstInstPaidOff
    FROM #t2 A
    INNER JOIN LF_LMSMaster..Payment P
        ON P.LoanID = A.LoanID
       AND P.PaymentMode IN ('A','D','B')
       AND P.PaymentType NOT IN ('3','~','Q')
       AND P.InstallmentNumber = 1
       AND P.AttemptNo >= 1
       AND P.PaymentDate <= GETDATE()
       AND P.PaymentStatus IN ('D','R','S','B')
) K
GROUP BY
    Application_ID,
    PortfolioID,
    LoanID;


/* ---------------------------------------------------------
   Enrich #t2 with:
   1) maturity flag: is_loan_first_install
   2) FPDAA (default NULL/unknown -> 0, per your earlier preference)
   3) FPDAA_matured: only populated when is_loan_first_install = 1
--------------------------------------------------------- */

DROP TABLE IF EXISTS #t2_perf;
SELECT
    A.*,

    /* First-installment (maturity) flag */
    CASE
        WHEN A.LoanStatus NOT IN ('V','W','G','K')
             AND NOT (
                 inst.iPaymentMode = 144
                 AND inst.Pending = 1
                 AND inst.DueDate >= CAST(GETDATE() AS date)
             )
        THEN 1 ELSE 0
    END AS is_loan_first_install,

    /* FPDAA (NULL -> 0). This is a per-row flag for modeling / general use. */
    COALESCE(pay.FPDAA_raw, 0) AS FPDAA,

    /* Metrics-safe FPDAA: only evaluate when mature; otherwise NULL */
    CASE
        WHEN A.LoanStatus NOT IN ('V','W','G','K')
             AND NOT (
                 inst.iPaymentMode = 144
                 AND inst.Pending = 1
                 AND inst.DueDate >= CAST(GETDATE() AS date)
             )
        THEN COALESCE(pay.FPDAA_raw, 0)
        ELSE NULL
    END AS FPDAA_matured

INTO #t2_perf
FROM #t2 A

/* Pull first installment attributes (for maturity logic) */
OUTER APPLY (
    SELECT TOP 1
        I.DueDate,
        I.iPaymentMode,
        CASE WHEN I.Status = 684 THEN 1 ELSE 0 END AS Pending
    FROM LF_LMSMaster..Installments I
    WHERE I.LoanID = A.LoanID
      AND I.InstallmentNumber = 1
    ORDER BY I.DueDate DESC, I.InstallmentID DESC
) inst

/* Compute FPDAA_raw using your “1 - MAX(paid_off)” logic, per LoanID */
OUTER APPLY (
    SELECT
        1 - MAX(CASE WHEN P.PaymentStatus = 'D' THEN 1 ELSE 0 END) AS FPDAA_raw
    FROM LF_LMSMaster..Payment P
    WHERE P.LoanID = A.LoanID
      AND P.PaymentMode IN ('A','D','B')
      AND P.PaymentType NOT IN ('3','~','Q')
      AND P.InstallmentNumber = 1
      AND P.AttemptNo >= 1
      AND P.PaymentDate <= GETDATE()
      AND P.PaymentStatus IN ('D','R','S','B')
) pay;

-------- spot check FPDAA
SELECT
    AVG(CAST(FPDAA_matured AS float)) AS FPDAA_rate
FROM #t2_perf
WHERE is_loan_first_install = 1;

--------------- RAW t2 app table join with IBVStatus ID ---------------
DROP TABLE IF EXISTS #t2_ibv;
SELECT ibv.IBVStatusID, IBV.DateCreated, A1.*
INTO #t2_ibv
FROM #t2_perf AS A1 LEFT JOIN [LF_BankData].[dbo].[IBVStatus] AS ibv ON A1.CustomerSSN = ibv.AccountNumber
--ibv.IBVStatusID, ibv.DateCreated

drop table if exists #t2_ibv_dedup
SELECT *
into #t2_ibv_dedup
FROM (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY LoanID ORDER BY DATEDIFF(day, ApplicationDate, DateCreated)) AS row_number
 FROM #t2_ibv
) AS t
WHERE t.row_number = 1

DROP TABLE IF EXISTS #ibv_to_apps;
SELECT rz.IBVToken, t1.*
INTO #ibv_to_apps
FROM #t2_ibv_dedup AS t1
JOIN (
    SELECT IBVToken
    FROM BankuityPostOnboarding.dbo.SpeedyAnalysis
    WHERE ExperimentName = 'loonie_rerun_V3'
) rz
  ON t1.IBVStatusID = rz.IBVToken;

SELECT *
FROM #ibv_to_apps
WHERE FPDAA_matured IS NULL